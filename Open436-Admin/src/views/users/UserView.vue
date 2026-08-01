<template>
  <div class="user-view">
    <div class="page-header">
      <h2>用户管理</h2>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索用户名/昵称/学号" clearable style="width:240px" prefix-icon="Search" @input="handleSearch" />
      <el-select v-model="roleFilter" placeholder="角色筛选" clearable style="width:140px" @change="handleSearch">
        <el-option label="管理员" value="admin" />
        <el-option label="用户" value="user" />
        <el-option label="浏览" value="viewer" />
      </el-select>
      <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width:140px" @change="handleSearch">
        <el-option label="待审核" value="pending" />
        <el-option label="已通过" value="active" />
        <el-option label="未通过" value="rejected" />
      </el-select>
      <div style="flex:1"></div>
      <el-button type="success" :disabled="!selectedIds.length" @click="handleBatchApprove">
        <el-icon><Check /></el-icon>审核通过
      </el-button>
      <el-button type="primary" :disabled="selectedIds.length !== 1" @click="handleOpenRoleDialog">
        <el-icon><UserFilled /></el-icon>权限分配
      </el-button>
      <el-button type="warning" :disabled="!selectedIds.length" @click="handleBatchResetPwd">
        <el-icon><Key /></el-icon>重置密码
      </el-button>
      <el-button type="danger" :disabled="!selectedIds.length" @click="handleBatchDisable">
        <el-icon><Close /></el-icon>禁用
      </el-button>
      <el-button type="danger" plain :disabled="!selectedIds.length" @click="handleBatchDelete">
        <el-icon><Delete /></el-icon>删除
      </el-button>
    </div>

    <!-- 表格 -->
    <el-table :data="filteredUsers" stripe v-loading="loading" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="用户" min-width="180">
        <template #default="{ row }">
          <div style="display:flex;align-items:center;gap:10px">
            <el-avatar :size="32" :src="row.avatar">{{ (row.username || '?')[0] }}</el-avatar>
            <div>
              <div style="font-weight:500">{{ row.nickname || row.username }}</div>
              <div style="font-size:12px;color:#909399">@{{ row.username }}</div>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="realName" label="真实姓名" width="100" />
      <el-table-column prop="studentId" label="学号" width="120" />
      <el-table-column prop="major" label="专业" width="120" />
      <el-table-column prop="phone" label="电话" width="120" />
      <el-table-column label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="roleTagType[row.role]" size="small">{{ roleLabels[row.role] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType[row.status]" size="small">{{ statusLabels[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="注册时间" width="160">
        <template #default="{ row }">
          {{ formatDate(row.createdAt || row.gmtCreate) }}
        </template>
      </el-table-column>
    </el-table>

    <div style="display:flex;justify-content:flex-end;margin-top:16px">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadUsers"
      />
    </div>

    <!-- 权限分配对话框 -->
    <el-dialog v-model="showRoleDialog" title="权限分配" width="400px" destroy-on-close>
      <div v-if="roleTarget" style="margin-bottom:16px">
        <span>用户：</span>
        <el-tag size="small">{{ roleTarget.nickname || roleTarget.username }}</el-tag>
        <span style="color:#909399;margin-left:8px">@{{ roleTarget.username }}</span>
      </div>
      <el-form label-width="60px">
        <el-form-item label="角色">
          <el-radio-group v-model="selectedRole" style="width:100%">
            <el-radio-button value="viewer">浏览</el-radio-button>
            <el-radio-button value="user">用户</el-radio-button>
            <el-radio-button value="admin">管理员</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <div style="background:#f5f7fa;padding:12px;border-radius:8px;margin-top:12px">
          <div style="font-size:13px;color:#606266;margin-bottom:8px">权限说明：</div>
          <div style="font-size:12px;color:#909399">
            <div><b>浏览</b>：仅可浏览论坛内容</div>
            <div><b>用户</b>：论坛发帖 + 算法做题</div>
            <div><b>管理员</b>：全部权限</div>
          </div>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="showRoleDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleRoleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="showResetDialog" title="重置密码" width="400px" destroy-on-close>
      <el-form ref="resetFormRef" :model="resetForm" :rules="resetRules" label-width="80px">
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="resetForm.newPassword" type="password" placeholder="6-32个字符" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showResetDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleResetSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUserList, updateUserStatus, updateUserRole, resetPassword, deleteUser, batchDeleteUsers, batchUpdateUserStatus } from '@/api/users'

const loading = ref(false)
const submitting = ref(false)
const users = ref([])
const keyword = ref('')
const roleFilter = ref('')
const statusFilter = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)
const selectedIds = ref([])

// 角色相关
const showRoleDialog = ref(false)
const roleTarget = ref(null)
const selectedRole = ref('user')

// 重置密码相关
const showResetDialog = ref(false)
const resetFormRef = ref(null)
const resetTargetIds = ref([])
const resetForm = reactive({ newPassword: '' })
const resetRules = {
  newPassword: [{ required: true, message: '请输入新密码', trigger: 'blur' }, { min: 6, max: 32, message: '6-32个字符', trigger: 'blur' }]
}

const roleLabels = { admin: '管理员', user: '用户', viewer: '浏览' }
const roleTagType = { admin: 'danger', user: '', viewer: 'info' }
const statusLabels = { pending: '待审核', active: '已通过', rejected: '未通过' }
const statusTagType = { pending: 'warning', active: 'success', rejected: 'info' }

function formatDate(dateStr) {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch {
    return dateStr
  }
}

function handleSelectionChange(rows) {
  selectedIds.value = rows.map(r => r.id)
}

const filteredUsers = computed(() => {
  let list = users.value
  if (keyword.value) {
    const kw = keyword.value.toLowerCase()
    list = list.filter(u =>
      (u.username || '').toLowerCase().includes(kw) ||
      (u.nickname || '').toLowerCase().includes(kw) ||
      (u.studentId || '').includes(kw)
    )
  }
  if (roleFilter.value) list = list.filter(u => u.role === roleFilter.value)
  if (statusFilter.value) list = list.filter(u => u.status === statusFilter.value)
  return list
})

function handleSearch() {
  page.value = 1
}

async function loadUsers() {
  loading.value = true
  try {
    const res = await getUserList({ page: page.value, size: pageSize })
    const data = res.data || res
    users.value = data.list || data.records || data || []
    total.value = data.total || users.value.length
  } catch (e) {
    ElMessage.error(e?.message || '加载用户列表失败')
  } finally {
    loading.value = false
  }
}

// ──────────── 批量操作 ────────────

async function handleBatchApprove() {
  try {
    await ElMessageBox.confirm(`确定通过选中的 ${selectedIds.value.length} 位用户？`, '审核确认', { type: 'warning' })
    await batchUpdateUserStatus(selectedIds.value, { status: 'active' })
    ElMessage.success('审核通过')
    selectedIds.value = []
    loadUsers()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e?.message || '操作失败')
  }
}

async function handleBatchDisable() {
  try {
    await ElMessageBox.confirm(`确定禁用选中的 ${selectedIds.value.length} 位用户？`, '禁用确认', { type: 'warning' })
    await batchUpdateUserStatus(selectedIds.value, { status: 'rejected' })
    ElMessage.success('已禁用')
    selectedIds.value = []
    loadUsers()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e?.message || '操作失败')
  }
}

function handleOpenRoleDialog() {
  if (selectedIds.value.length !== 1) return
  const user = users.value.find(u => u.id === selectedIds.value[0])
  if (!user) return
  roleTarget.value = user
  selectedRole.value = user.role || 'user'
  showRoleDialog.value = true
}

async function handleRoleSubmit() {
  submitting.value = true
  try {
    await updateUserRole(roleTarget.value.id, { role: selectedRole.value })
    roleTarget.value.role = selectedRole.value
    ElMessage.success('权限分配成功')
    showRoleDialog.value = false
  } catch (e) {
    ElMessage.error(e?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

function handleBatchResetPwd() {
  resetTargetIds.value = [...selectedIds.value]
  resetForm.newPassword = ''
  showResetDialog.value = true
}

async function handleResetSubmit() {
  const valid = await resetFormRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    for (const id of resetTargetIds.value) {
      await resetPassword(id, { newPassword: resetForm.newPassword })
    }
    ElMessage.success(`已重置 ${resetTargetIds.value.length} 位用户的密码`)
    showResetDialog.value = false
  } catch (e) {
    ElMessage.error(e?.message || '重置失败')
  } finally {
    submitting.value = false
  }
}

async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 位用户？此操作不可恢复！`, '删除确认', { type: 'warning' })
    await batchDeleteUsers(selectedIds.value)
    ElMessage.success('删除成功')
    selectedIds.value = []
    loadUsers()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e?.message || '删除失败')
  }
}

onMounted(loadUsers)
</script>

<style scoped>
.user-view {
  padding: 0;
}
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}
.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
</style>
