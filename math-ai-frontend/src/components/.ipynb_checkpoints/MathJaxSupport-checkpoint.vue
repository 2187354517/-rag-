<template>
  <div ref="mathjaxContainer" v-html="processedContent" class="math-content"></div>
</template>

<script>
import { ref, onMounted, watch, nextTick, computed, onBeforeUnmount } from 'vue';

export default {
  name: 'MathJaxSupport',
  props: {
    content: {
      type: String,
      default: '',
      required: true
    }
  },
  setup(props) {
    const mathjaxContainer = ref(null);
    let mathjaxScript = null;
    let mathjaxReady = false;

    // 安全处理内容
    const processedContent = computed(() => {
      return props.content
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    });

    // 渲染数学公式
    const renderMathJax = () => {
      if (!mathjaxReady || !mathjaxContainer.value) return;
      
      try {
        if (window.MathJax && window.MathJax.typesetPromise) {
          window.MathJax.typesetPromise([mathjaxContainer.value])
            .then(() => {
              // 渲染完成后调整公式样式
              adjustMathJaxStyles();
            })
            .catch(err => console.warn('MathJax typeset error:', err));
        } else {
          console.warn('MathJax not fully loaded yet');
          setTimeout(renderMathJax, 100);
        }
      } catch (err) {
        console.error('MathJax rendering error:', err);
      }
    };

    // 调整MathJax渲染后的样式
    const adjustMathJaxStyles = () => {
      if (!mathjaxContainer.value) return;
      
      // 移除所有MathJax元素上的滚动条相关样式
      const mathElements = mathjaxContainer.value.querySelectorAll('.MathJax, .MJXc-display');
      mathElements.forEach(el => {
        el.style.overflow = 'visible';
        el.style.maxWidth = 'none';
      });
    };

    // 初始化MathJax配置
    const configureMathJax = () => {
      window.MathJax = {
        startup: {
          ready: () => {
            window.MathJax.startup.defaultReady();
            window.MathJax.startup.promise.then(() => {
              mathjaxReady = true;
              renderMathJax();
            });
          }
        },
        tex: {
          inlineMath: [['$', '$'], ['\\(', '\\)']],
          displayMath: [['$$', '$$'], ['\\[', '\\]']],
          processEscapes: true
        },
        options: {
          enableMenu: false,
          skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
          // 禁用自动换行
          linebreaks: {
            automatic: false,
            width: '100%'
          }
        },
        chtml: {
          // 禁用缩放
          scale: 1,
          // 禁用自适应布局
          matchFontHeight: false
        }
      };
    };

    // 加载MathJax脚本
    const loadMathJax = () => {
      if (window.MathJax && window.MathJax.typesetPromise) {
        mathjaxReady = true;
        renderMathJax();
        return;
      }

      configureMathJax();

      mathjaxScript = document.createElement('script');
      mathjaxScript.id = 'MathJax-script';
      mathjaxScript.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js';
      mathjaxScript.async = true;
      mathjaxScript.onload = () => {
        if (!window.MathJax) {
          console.error('MathJax failed to load');
          return;
        }
      };
      mathjaxScript.onerror = () => console.error('Failed to load MathJax');
      document.head.appendChild(mathjaxScript);
    };

    // 防抖处理渲染
    const debouncedRender = debounce(renderMathJax, 100);

    onMounted(() => {
      loadMathJax();
      nextTick(debouncedRender);
    });

    watch(() => props.content, () => {
      nextTick(debouncedRender);
    });

    onBeforeUnmount(() => {
      if (mathjaxScript && document.head.contains(mathjaxScript)) {
        document.head.removeChild(mathjaxScript);
      }
      mathjaxReady = false;
    });

    return {
      mathjaxContainer,
      processedContent
    };
  }
};

// 简单的防抖函数
function debounce(fn, delay) {
  let timer = null;
  return function(...args) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}
</script>

<style scoped>
.math-content {
  width: 100%;
  overflow: visible;
}

/* 数学公式样式优化 - 移除所有滚动条 */
:deep(.MathJax),
:deep(.MJXc-display) {
  overflow: visible !important;
  max-width: none !important;
  width: auto !important;
  display: inline-block !important;
}

/* 行内公式样式 */
:deep(.MathJax_Inline) {
  display: inline !important;
  white-space: nowrap;
}

/* 块级公式样式 */
:deep(.MathJax_Display) {
  display: block !important;
  margin: 1em 0;
  text-align: center;
  white-space: normal;
}

/* 公式容器样式 */
:deep(.MJXc-display) {
  display: inline-block !important;
  margin: 0 !important;
  padding: 0 !important;
  width: auto !important;
}
</style>