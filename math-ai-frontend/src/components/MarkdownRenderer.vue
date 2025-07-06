<template>
  <div 
    class="markdown-renderer" 
    ref="markdownContainer" 
    :class="{ rendered: isRendered }"
    v-html="renderedContent"
  ></div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import DOMPurify from 'dompurify'
import markdownItKatex from '@traptitech/markdown-it-katex'
import 'katex/dist/katex.min.css'

const props = defineProps({
  content: {
    type: String,
    required: true
  },
  sanitize: {
    type: Boolean,
    default: true
  }
})

const markdownContainer = ref(null)
const renderedContent = ref('')
const isRendered = ref(false)
let observer = null

// 配置 markdown-it
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: (code, lang) => {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext'
    return hljs.highlight(code, { language }).value
  }
})

// 添加 Katex 插件支持 LaTeX 数学公式
// 修改后的插件配置（文件第28行附近）
md.use(markdownItKatex, {
  throwOnError: false,
  errorColor: '#cc0000',
  strict: false,
  delimiters: [
    { left: "$$", right: "$$", display: true },    // 默认块级公式
    { left: "$", right: "$", display: false },     // 默认行内公式
    { left: "\\[", right: "\\]", display: true },  // 支持 \[...\] 块级
    { left: "\\(", right: "\\)", display: false }  // 支持 \(...\) 行内
  ]
})

// 初始化 IntersectionObserver 用于图片懒加载
const initObserver = () => {
  if (typeof IntersectionObserver === 'undefined') return

  observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target
        img.src = img.dataset.src
        img.onload = () => {
          img.classList.add('lazyloaded')
        }
        observer.unobserve(img)
      }
    })
  }, {
    rootMargin: '200px',
    threshold: 0.01
  })
}

// 渲染 Markdown 内容
const renderMarkdown = async () => {
  if (!props.content || !markdownContainer.value) return

  try {
    isRendered.value = false
    // 使用 markdown-it 解析 Markdown
    let html = md.render(props.content);
    // 安全净化处理
    if (props.sanitize) {
      html = DOMPurify.sanitize(html, {
        ADD_ATTR: ['target', 'data-display'],
        ADD_TAGS: ['math', 'maction', 'maligngroup', 'malignmark', 'menclose', 
                  'merror', 'mfenced', 'mfrac', 'mi', 'mlongdiv', 'mmultiscripts',
                  'mn', 'mo', 'mover', 'mpadded', 'mphantom', 'mroot', 'mrow',
                  'ms', 'mscarries', 'mscarry', 'mscarries', 'msgroup', 'mstack',
                  'mlongdiv', 'msline', 'mstack', 'mspace', 'msqrt', 'msrow',
                  'mstack', 'mstyle', 'msub', 'msup', 'msubsup', 'mtable', 'mtd',
                  'mtext', 'mtr', 'munder', 'munderover', 'semantics', 'annotation',
                  'annotation-xml'],
        FORBID_TAGS: ['style', 'script', 'iframe']
      })
    }
    
    // 处理图片懒加载
    const parser = new DOMParser()
    const doc = parser.parseFromString(html, 'text/html')
    const images = doc.querySelectorAll('img')

    images.forEach(img => {
      const src = img.getAttribute('src')
      if (src && !src.startsWith('data:')) {
        img.setAttribute('data-src', src)
        img.removeAttribute('src')
        img.classList.add('lazyload')
        // 添加占位背景
        img.style.backgroundColor = '#f5f5f5'
      }
    })

    renderedContent.value = doc.body.innerHTML
    
    await nextTick()
    
    // 动态加载图片的懒加载
    if (typeof IntersectionObserver !== 'undefined') {
      const lazyImages = markdownContainer.value.querySelectorAll('img[data-src]')
      lazyImages.forEach(img => {
        observer?.observe(img)
      })
    }

    // 标记渲染完成
    isRendered.value = true
  } catch (error) {
    console.error('Markdown 渲染错误:', error)
    renderedContent.value = '<p class="error">内容渲染失败</p>'
    isRendered.value = true
  }
}

onMounted(() => {
  initObserver()
  renderMarkdown()
})

onBeforeUnmount(() => {
  observer?.disconnect()
})

watch(() => props.content, () => {
  renderMarkdown()
}, { immediate: true })
</script>

<style scoped>
.markdown-renderer {
  min-width: 400px;
  white-space: normal; /* Changed from nowrap to normal */
  overflow-x: auto;
  line-height: 1.6;
  word-wrap: break-word;
  opacity: 0;
  visibility: hidden;
  transition: 
    opacity 0.3s ease,
    visibility 0.3s ease;
}

.markdown-renderer.rendered {
  opacity: 1;
  visibility: visible;
}

.markdown-renderer :deep() > * {
  margin-top: 0;
  margin-bottom: 0.5em;
}

.markdown-renderer :deep() h1,
.markdown-renderer :deep() h2,
.markdown-renderer :deep() h3,
.markdown-renderer :deep() h4 {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-renderer :deep() h1 {
  font-size: 2em;
  border-bottom: 1.5px solid black !important;
  padding-bottom: 0.3em;
  min-width: 750px;
}

.markdown-renderer :deep() h2 {
  font-size: 1.5em;
  border-bottom: 1.5px solid black !important;
  padding-bottom: 0.3em;
  min-width: 750px;
}

.markdown-renderer :deep() ul,
.markdown-renderer :deep() ol {
  padding-left: 2em;
}

.markdown-renderer :deep() blockquote {
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
  margin-left: 0;
}

.markdown-renderer :deep() pre {
  background-color: #f6f8fa;
  border-radius: 6px;
  padding: 16px;
  overflow: auto;
}

.markdown-renderer :deep() code {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  background-color: rgba(27, 31, 35, 0.05);
  border-radius: 3px;
  padding: 0.2em 0.4em;
  font-size: 85%;
}

.markdown-renderer :deep() pre code {
  background-color: transparent;
  padding: 0;
}

.markdown-renderer :deep() img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 1em auto;
  border-radius: 4px;
  transition: 
    opacity 0.3s ease,
    background-color 0.3s ease;
}

.markdown-renderer :deep() img.lazyload {
  opacity: 1;
  min-height: 100px;
  background-color: #f5f5f5;
}

.markdown-renderer :deep() img.lazyloaded {
  background-color: transparent;
}

.markdown-renderer :deep() a {
  color: #0366d6;
  text-decoration: none;
}

.markdown-renderer :deep() a:hover {
  text-decoration: underline;
}

.markdown-renderer :deep() table {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
  display: block;
  overflow-x: auto;
}

.markdown-renderer :deep() th,
.markdown-renderer :deep() td {
  border: 1px solid #dfe2e5;
  padding: 6px 13px;
}

.markdown-renderer :deep() th {
  background-color: #f6f8fa;
  font-weight: 600;
}

.markdown-renderer :deep() tr {
  background-color: #fff;
  border-top: 1px solid #c6cbd1;
}

.markdown-renderer :deep() tr:nth-child(2n) {
  background-color: #f6f8fa;
}

.error {
  color: #d73a49;
  padding: 8px;
  background-color: #ffeef0;
  border-radius: 4px;
}

/* 改进的 Katex 公式样式 */
.markdown-renderer :deep() .katex {
  font-size: 1.1em;
  text-align: center;
}

.markdown-renderer :deep() .katex-display {
  margin: 1em 0;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 0.5em 0;
  text-align: center;
}

.markdown-renderer :deep() .katex-display > .katex {
  display: inline-block;
  text-align: center;
  white-space: nowrap;
}

.markdown-renderer :deep() .katex-error {
  color: #cc0000;
  background-color: #fff0f0;
  padding: 2px 4px;
  border-radius: 3px;
  display: inline-block;
}

/* 行内公式样式 */
.markdown-renderer :deep() .katex-inline {
  font-size: 1.05em;
  padding: 0 0.1em;
}

/* 确保公式容器不会换行 */
.markdown-renderer :deep() .math-block {
  white-space: nowrap;
  overflow-x: auto;
  display: block;
  text-align: center;
}
</style>