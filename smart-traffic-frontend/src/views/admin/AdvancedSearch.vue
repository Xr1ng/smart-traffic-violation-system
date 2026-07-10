<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">综合查询</h2>
    </div>

    <el-card>
      <el-form :model="query" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-form-item label="车牌号">
              <el-input v-model="query.plate" placeholder="输入车牌号" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="违章地点">
              <el-input v-model="query.location" placeholder="输入违章地点" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="违章类型">
              <el-select v-model="query.type" placeholder="选择违章类型" clearable style="width:100%">
                <el-option label="闯红灯" value="闯红灯" />
                <el-option label="超速" value="超速" />
                <el-option label="违停" value="违停" />
                <el-option label="压线" value="压线" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="违章时间">
              <el-date-picker
                v-model="query.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始"
                end-placeholder="结束"
                value-format="YYYY-MM-DD"
                style="width:100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="24" style="text-align:right">
            <el-button type="primary" @click="handleSearch">查询</el-button>
            <el-button @click="resetQuery">重置</el-button>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <el-card style="margin-top:16px">
      <el-table :data="results" border stripe v-loading="loading" empty-text="请点击查询按钮搜索">
        <el-table-column prop="violation_no" label="违章编号" min-width="170" />
        <el-table-column prop="plate_no" label="车牌号" width="120" />
        <el-table-column prop="violation_type" label="违章类型" width="100" />
        <el-table-column prop="location_text" label="违章地点" min-width="160" />
        <el-table-column prop="occurred_at" label="违章时间" width="180" />
        <el-table-column prop="fine_amount" label="罚款（元）" width="100" />
        <el-table-column prop="points" label="扣分" width="80" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'pending'" type="info">待处理</el-tag>
            <el-tag v-else type="info">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div style="display:flex;justify-content:flex-end;margin-top:16px" v-if="total > 0">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @change="handleSearch"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { fetchViolations } from '@/api/violation'
import { buildViolationQuery } from '@/utils/contracts'

const query = reactive({ plate: '', location: '', type: '', dateRange: null })
const results = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

async function handleSearch() {
  loading.value = true
  try {
    const res = await fetchViolations(buildViolationQuery(query, page.value, pageSize.value))
    results.value = res.data.items
    total.value = res.data.total
  } catch { /* handled */ }
  finally { loading.value = false }
}

function resetQuery() {
  Object.keys(query).forEach(k => query[k] = k === 'dateRange' ? null : '')
  results.value = []
  total.value = 0
}
</script>
