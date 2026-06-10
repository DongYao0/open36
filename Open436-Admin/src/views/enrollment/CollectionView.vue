<template>
  <div class="collection-view">
    <!-- 第一层：作业列表 -->
    <template v-if="!selectedAssignment">
      <div class="page-header"><h2>作业收集</h2></div>

      <!-- 统计卡片 -->
      <el-row :gutter="20" style="margin-bottom:20px">
        <el-col :span="6">
          <StatCard label="总作业数" :value="stats.total" icon="Document" icon-bg="#e3f2fd" icon-color="#1976D2" />
        </el-col>
        <el-col :span="6">
          <StatCard label="待收集" :value="stats.collecting" icon="Clock" icon-bg="#fff3e0" icon-color="#ff9800" />
        </el-col>
        <el-col :span="6">
          <StatCard label="已收集" :value="stats.collected" icon="CircleCheck" icon-bg="#e8f5e9" icon-color="#4caf50" />
        </el-col>
        <el-col :span="6">
          <StatCard label="提交率" :value="stats.submitRate + '%'" icon="TrendCharts" icon-bg="#f3e5f5" icon-color="#9c27b0" />
        </el-col>
      </el-row>

      <!-- 作业列表 -->
      <el-table :data="assignments" stripe v-loading="loading" @row-click="enterAssignment">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="作业标题" min-width="200" />
        <el-table-column prop="deadline" label="截止时间" width="160" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType[row.status]" size="small">{{ statusLabels[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="submittedCount" label="已提交" width="80" />
        <el-table-column prop="totalCount" label="总人数" width="80" />
        <el-table-column label="提交率" width="100">
          <template #default="{ row }">
            <el-progress :percentage="row.totalCount ? Math.round(row.submittedCount / row.totalCount * 100) : 0" :stroke-width="8" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="enterAssignment(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="display:flex;justify-content:flex-end;margin-top:16px">
        <el-pagination v-model:current-page="page" :page-size="10" :total="total" layout="total, prev, pager, next" @current-change="loadList" />
      </div>
    </template>

    <!-- 第二层：人员提交状态列表 -->
    <template v-else-if="!selectedStudent">
      <div class="page-header">
        <div class="breadcrumb">
          <el-button link @click="selectedAssignment = null">
            <el-icon><ArrowLeft /></el-icon> 返回作业列表
          </el-button>
          <span class="separator">/</span>
          <span class="current">{{ selectedAssignment.title }}</span>
        </div>
      </div>

      <el-card class="assignment-info">
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="作业标题">{{ selectedAssignment.title }}</el-descriptions-item>
          <el-descriptions-item label="截止时间">{{ selectedAssignment.deadline }}</el-descriptions-item>
          <el-descriptions-item label="提交情况">
            {{ selectedAssignment.submittedCount }} / {{ selectedAssignment.totalCount }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <div class="toolbar" style="margin-top:16px">
        <el-input v-model="studentKeyword" placeholder="搜索姓名/学号" clearable style="width:200px" prefix-icon="Search" @input="loadStudents" />
        <el-radio-group v-model="studentFilter" @change="loadStudents">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="submitted">已提交</el-radio-button>
          <el-radio-button value="unsubmitted">未提交</el-radio-button>
        </el-radio-group>
      </div>

      <el-table :data="students" stripe v-loading="studentLoading" @row-click="enterStudent">
        <el-table-column prop="studentName" label="姓名" width="100" />
        <el-table-column prop="studentNo" label="学号" width="130" />
        <el-table-column prop="major" label="专业" width="120" />
        <el-table-column prop="direction" label="方向" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="primary">{{ row.direction }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="提交状态" width="100">
          <template #default="{ row }">
            <el-tag :type="submitStatusType[row.status]" size="small">{{ submitStatusLabel[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="submittedAt" label="提交时间" width="160" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="enterStudent(row)">
              {{ row.status === 'submitted' || row.status === 'graded' ? '查看' : '催交' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </template>

    <!-- 第三层：查看学生作业内容 -->
    <template v-else>
      <div class="page-header">
        <div class="breadcrumb">
          <el-button link @click="selectedStudent = null">
            <el-icon><ArrowLeft /></el-icon> 返回人员列表
          </el-button>
          <span class="separator">/</span>
          <el-button link @click="selectedAssignment = null; selectedStudent = null">
            {{ selectedAssignment.title }}
          </el-button>
          <span class="separator">/</span>
          <span class="current">{{ selectedStudent.studentName }}</span>
        </div>
      </div>

      <el-row :gutter="20">
        <!-- 左侧：学生信息 -->
        <el-col :span="8">
          <el-card>
            <template #header>
              <span>学生信息</span>
            </template>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="姓名">{{ selectedStudent.studentName }}</el-descriptions-item>
              <el-descriptions-item label="学号">{{ selectedStudent.studentNo }}</el-descriptions-item>
              <el-descriptions-item label="专业">{{ selectedStudent.major }}</el-descriptions-item>
              <el-descriptions-item label="方向">
                <el-tag size="small" type="primary">{{ selectedStudent.direction }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="提交状态">
                <el-tag :type="submitStatusType[selectedStudent.status]" size="small">
                  {{ submitStatusLabel[selectedStudent.status] }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="提交时间">{{ selectedStudent.submittedAt || '-' }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>

        <!-- 右侧：作业内容 -->
        <el-col :span="16">
          <el-card>
            <template #header>
              <span>作业内容</span>
            </template>

            <div v-if="selectedStudent.status === 'unsubmitted'" class="empty-content">
              <el-empty description="该学生尚未提交作业" />
              <div style="text-align:center;margin-top:16px">
                <el-button type="warning" @click="handleReminder(selectedStudent)">发送催交通知</el-button>
              </div>
            </div>

            <div v-else class="submission-content">
              <div v-if="selectedStudent.content" class="text-content">
                <h4>提交内容</h4>
                <p>{{ selectedStudent.content }}</p>
              </div>

              <div v-if="selectedStudent.files?.length" class="file-list">
                <h4>附件</h4>
                <div v-for="file in selectedStudent.files" :key="file.name" class="file-item">
                  <el-icon :size="20"><Document /></el-icon>
                  <div class="file-info">
                    <span class="file-name">{{ file.name }}</span>
                    <span class="file-size">{{ file.size }}</span>
                  </div>
                  <el-button type="primary" link size="small">下载</el-button>
                </div>
              </div>

              <div v-if="selectedStudent.codeContent" class="code-content">
                <h4>代码提交</h4>
                <el-input :model-value="selectedStudent.codeContent" type="textarea" :rows="15" readonly />
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import StatCard from '@/components/StatCard.vue'
import {
  getAssignmentList, getAssignmentStats,
  getSubmissions, getSubmissionDetail, sendReminder as apiSendReminder
} from '@/api/assignment'

const loading = ref(false)
const assignments = ref([])
const total = ref(0)
const page = ref(1)
const stats = ref({ total: 0, collecting: 0, collected: 0, submitRate: 0 })

// 第二层相关
const selectedAssignment = ref(null)
const studentLoading = ref(false)
const students = ref([])
const studentKeyword = ref('')
const studentFilter = ref('')

// 第三层相关
const selectedStudent = ref(null)

const statusLabels = { active: '进行中', ended: '已截止', pending: '待分发' }
const statusTagType = { active: 'warning', ended: 'success', pending: 'info' }

const submitStatusLabel = { submitted: '已提交', unsubmitted: '未提交' }
const submitStatusType = { submitted: 'warning', unsubmitted: 'info' }

async function loadStats() {
  try {
    const res = await getAssignmentStats()
    stats.value = res.data
  } catch (e) {
    console.error('加载统计失败', e)
  }
}

async function loadList() {
  loading.value = true
  try {
    const res = await getAssignmentList({ page: page.value, size: 10 })
    assignments.value = res.data.list
    total.value = res.data.total
  } catch (e) {
    console.error('加载作业列表失败', e)
  } finally {
    loading.value = false
  }
}

function enterAssignment(row) {
  selectedAssignment.value = row
  selectedStudent.value = null
  loadStudents()
}

async function loadStudents() {
  if (!selectedAssignment.value) return
  studentLoading.value = true
  try {
    const res = await getSubmissions(selectedAssignment.value.id, {
      keyword: studentKeyword.value,
      filter: studentFilter.value
    })
    students.value = res.data
  } catch (e) {
    console.error('加载提交列表失败', e)
  } finally {
    studentLoading.value = false
  }
}

async function enterStudent(row) {
  if (row.status === 'unsubmitted') {
    handleReminder(row)
    return
  }
  try {
    const res = await getSubmissionDetail(row.id)
    selectedStudent.value = res.data
  } catch (e) {
    ElMessage.error('获取提交详情失败')
  }
}

async function handleReminder(row) {
  try {
    await apiSendReminder(row.id)
    ElMessage.success('已发送催交通知')
  } catch (e) {
    ElMessage.error('催交失败')
  }
}

onMounted(() => {
  loadStats()
  loadList()
})
</script>

<style scoped>
.collection-view {
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
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}
.breadcrumb .separator {
  color: #999;
}
.breadcrumb .current {
  font-weight: 600;
  color: #303133;
}
.assignment-info {
  margin-bottom: 16px;
}
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.empty-content {
  padding: 40px 0;
}
.submission-content h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #303133;
}
.text-content {
  margin-bottom: 24px;
}
.text-content p {
  color: #666;
  line-height: 1.8;
  margin: 0;
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
}
.file-list {
  margin-bottom: 24px;
}
.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 8px;
}
.file-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.file-name {
  font-weight: 500;
  color: #303133;
}
.file-size {
  font-size: 12px;
  color: #999;
}
.code-content {
  margin-bottom: 24px;
}
</style>
