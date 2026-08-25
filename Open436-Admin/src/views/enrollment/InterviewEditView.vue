<template>
  <div class="interview-edit-view" v-loading="loading">
    <!-- 顶部导航 -->
    <div class="page-header">
      <el-button link @click="goBack">
        <el-icon><ArrowLeft /></el-icon>返回面试管理
      </el-button>
      <h2>编辑面试信息</h2>
    </div>

    <el-card v-if="detail" shadow="never" class="main-card">
      <!-- 候选人信息 -->
      <template #header>
        <div class="card-header">
          <span class="card-title">候选人信息</span>
          <el-tag :type="statusTagType[detail.status]" size="small">{{ statusLabels[detail.status] }}</el-tag>
        </div>
      </template>

      <el-descriptions :column="4" border>
        <el-descriptions-item label="姓名">{{ detail.realName }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ detail.username }}</el-descriptions-item>
        <el-descriptions-item label="学号">{{ detail.studentId }}</el-descriptions-item>
        <el-descriptions-item label="专业">{{ detail.major }}</el-descriptions-item>
        <el-descriptions-item label="自我介绍" :span="4">{{ detail.selfIntro || '暂无' }}</el-descriptions-item>
        <el-descriptions-item label="技能标签" :span="4">
          <el-tag v-for="skill in detail.skills?.split(',')" :key="skill" style="margin:2px 4px" v-if="detail.skills">{{ skill.trim() }}</el-tag>
          <span v-else style="color:#c0c4cc">暂无</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="never" class="main-card" style="margin-top:20px">
      <template #header>
        <span class="card-title">面试记录</span>
      </template>

      <el-form :model="form" label-width="80px" class="edit-form">
        <el-form-item label="面试记录">
          <el-input
            v-model="form.summary"
            type="textarea"
            :rows="10"
            placeholder="记录面试过程、综合评价、优点、不足等..."
          />
        </el-form-item>

        <el-form-item label="意向">
          <el-input v-model="form.direction" placeholder="如：前端/后端/算法/运维" />
        </el-form-item>
      </el-form>

      <div class="form-actions">
        <el-button @click="goBack">取消</el-button>
        <el-button type="primary" size="large" @click="submitForm" :disabled="submitting">
          <el-icon><Check /></el-icon>保存
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getInterviewDetail, recordInterview } from '@/api/interview'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const detail = ref(null)
const form = ref({
  enrollmentId: null,
  direction: '',
  summary: ''
})

const statusLabels = { pending: '待面试', passed: '已通过', failed: '未通过' }
const statusTagType = { pending: 'warning', passed: 'success', failed: 'danger' }

async function loadDetail() {
  loading.value = true
  try {
    const enrollmentId = route.params.enrollmentId
    const res = await getInterviewDetail(enrollmentId)
    detail.value = res.data
    form.value = {
      enrollmentId: res.data.enrollmentId,
      direction: res.data.direction || '',
      summary: res.data.summary || ''
    }
  } catch {
    ElMessage.error('加载数据失败')
    goBack()
  } finally {
    loading.value = false
  }
}

async function submitForm() {
  if (!form.value.summary) {
    ElMessage.warning('请填写面试记录')
    return
  }
  submitting.value = true
  try {
    await recordInterview({
      enrollmentId: form.value.enrollmentId,
      direction: form.value.direction,
      summary: form.value.summary
    })
    ElMessage.success('保存成功')
    goBack()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    submitting.value = false
  }
}

function goBack() {
  router.push('/enrollment/interview')
}

onMounted(loadDetail)
</script>

<style scoped>
.interview-edit-view {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}
.main-card {
  border-radius: 8px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-title {
  font-size: 16px;
  font-weight: 600;
}
.edit-form {
  margin-top: 20px;
}
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}
</style>
