export function buildFileTree(files) {
  const tree = []
  const pathMap = {}

  files.forEach((file) => {
    // 统一处理 Windows 和 Unix 路径分隔符
    const normalizedPath = file.rel_path.replace(/\\/g, '/')
    const parts = normalizedPath.split('/')
    let currentLevel = tree

    parts.forEach((part, index) => {
      const fullPath = parts.slice(0, index + 1).join('/')
      const isFile = index === parts.length - 1

      if (!pathMap[fullPath]) {
        const node = {
          label: part,
          children: [],
          isFile,
          file: isFile ? file : null,
        }
        pathMap[fullPath] = node
        currentLevel.push(node)
      }

      currentLevel = pathMap[fullPath].children
    })
  })

  return tree
}

export function flattenTree(nodes, result = []) {
  nodes.forEach((node) => {
    if (node.isFile) {
      result.push(node.file)
    }
    if (node.children && node.children.length > 0) {
      flattenTree(node.children, result)
    }
  })
  return result
}
