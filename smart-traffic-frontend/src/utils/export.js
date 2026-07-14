import * as XLSX from 'xlsx'

/**
 * 通用 Excel 导出
 * @param {Array} data     - 数据数组
 * @param {Array} columns  - 列定义 [{ key: 'field', label: '列名', width?: 20 }]
 * @param {string} filename - 文件名（不含扩展名）
 */
export function exportToExcel(data, columns, filename = 'export') {
  const header = columns.map(c => c.label)
  const rows = data.map(row =>
    columns.map(c => {
      const val = row[c.key]
      return val !== undefined && val !== null ? String(val) : ''
    })
  )

  const sheet = XLSX.utils.aoa_to_sheet([header, ...rows])

  // 设置列宽
  const colWidths = columns.map(c => ({ wch: c.width || 20 }))
  sheet['!cols'] = colWidths

  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, sheet, 'Sheet1')
  XLSX.writeFile(wb, `${filename}.xlsx`)
}

/**
 * 格式化日期用于导出
 * @param {string|Date} t
 * @returns {string}
 */
export function formatExportTime(t) {
  return t ? new Date(t).toLocaleString('zh-CN') : ''
}
