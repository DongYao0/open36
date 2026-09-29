function protectSpreadsheetFormula(value) {
  const text = value == null ? '' : String(value)
  return /^[=+\-@]/.test(text) ? `'${text}` : text
}

function csvCell(value) {
  const text = protectSpreadsheetFormula(value).replace(/"/g, '""')
  return `"${text}"`
}

export function downloadCsv(filename, columns, rows) {
  const header = columns.map(column => csvCell(column.label)).join(',')
  const body = rows.map((row, rowIndex) => columns
    .map(column => csvCell(typeof column.value === 'function' ? column.value(row, rowIndex) : row[column.key]))
    .join(','))
  const csv = `\uFEFF${[header, ...body].join('\r\n')}`
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

export function exportDateStamp() {
  const now = new Date()
  const pad = value => String(value).padStart(2, '0')
  return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}`
}
