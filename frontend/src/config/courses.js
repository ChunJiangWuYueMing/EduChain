export const courseCatalog = Object.freeze([
  { code: 'BC401', name: '区块链技术及应用' },
  { code: 'CS201', name: '数据结构' },
  { code: 'CS301', name: '操作系统' },
  { code: 'CS302', name: '计算机网络' },
  { code: 'DB201', name: '数据库原理' },
  { code: 'AI301', name: '人工智能导论' },
])

export const courseNameMap = Object.freeze(
  Object.fromEntries(courseCatalog.map((course) => [course.code, course.name])),
)

export function courseDisplay(code) {
  const name = courseNameMap[code]
  return name ? `${code} ${name}` : code
}
