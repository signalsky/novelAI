const api = {
  async listNovels() {
    const res = await fetch("/api/novels");
    if (!res.ok) {
      throw new Error("load_failed");
    }
    return res.json();
  },
  async createNovel(title) {
    const res = await fetch("/api/novels", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });
    if (!res.ok) {
      throw new Error("create_failed");
    }
    return res.json();
  },
  async getNovel(id) {
    const res = await fetch(`/api/novels/${id}`);
    if (!res.ok) {
      throw new Error("load_failed");
    }
    return res.json();
  },
  async saveStory(id, payload) {
    const res = await fetch(`/api/novels/${id}/story`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error("save_failed");
    }
    return res.json();
  },
  async saveAdvanced(id, payload) {
    const res = await fetch(`/api/novels/${id}/advanced`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error("save_failed");
    }
    return res.json();
  },
  async optimize(payload) {
    const res = await fetch("/api/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error("optimize_failed");
    }
    return res.json();
  },
  async getChatHistory() {
    const res = await fetch("/api/chat/history");
    if (!res.ok) {
      throw new Error("chat_failed");
    }
    return res.json();
  },
  async sendChat(message) {
    const res = await fetch("/api/chat/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (!res.ok) {
      throw new Error("chat_failed");
    }
    return res.json();
  },
  async clearChat() {
    const res = await fetch("/api/chat/clear", { method: "POST" });
    if (!res.ok) {
      throw new Error("chat_failed");
    }
    return res.json();
  },
};

const dom = {
  novelList: document.getElementById("novel-list"),
  createBtn: document.getElementById("create-btn"),
  titleInput: document.getElementById("novel-title"),
  saveBtn: document.getElementById("save-btn"),
  status: document.getElementById("status"),
  optimizeModal: document.getElementById("optimize-modal"),
  optimizePrompt: document.getElementById("optimize-prompt"),
  optimizeResult: document.getElementById("optimize-result"),
  optimizeSubmit: document.getElementById("optimize-submit"),
  optimizeApply: document.getElementById("optimize-apply"),
  optimizeRevert: document.getElementById("optimize-revert"),
  optimizeClose: document.getElementById("optimize-close"),
  chatHistory: document.getElementById("chat-history"),
  chatInput: document.getElementById("chat-input"),
  chatSearch: document.getElementById("chat-search"),
  chatSend: document.getElementById("chat-send"),
  chatClear: document.getElementById("chat-clear"),
};

function setStatus(message) {
  if (!dom.status) return;
  dom.status.textContent = message;
}

let toastTimer = null;

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function markdownToHtml(markdown) {
  const escaped = escapeHtml(markdown || "");
  const parts = escaped.split("```");
  const htmlParts = parts.map((part, idx) => {
    const isCode = idx % 2 === 1;
    if (isCode) {
      let code = part;
      const firstNewline = code.indexOf("\n");
      if (firstNewline !== -1) {
        const firstLine = code.slice(0, firstNewline).trim();
        if (/^[a-zA-Z0-9_-]{1,30}$/.test(firstLine)) {
          code = code.slice(firstNewline + 1);
        }
      }
      return `<pre><code>${code}</code></pre>`;
    }

    let text = part;
    text = text.replace(
      /^######\s+(.+)$/gm,
      '<div class="md-heading md-h6">$1</div>'
    );
    text = text.replace(
      /^#####\s+(.+)$/gm,
      '<div class="md-heading md-h5">$1</div>'
    );
    text = text.replace(
      /^####\s+(.+)$/gm,
      '<div class="md-heading md-h4">$1</div>'
    );
    text = text.replace(/^###\s+(.+)$/gm, '<div class="md-heading md-h3">$1</div>');
    text = text.replace(/^##\s+(.+)$/gm, '<div class="md-heading md-h2">$1</div>');
    text = text.replace(/^#\s+(.+)$/gm, '<div class="md-heading md-h1">$1</div>');
    text = text.replaceAll(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    text = text.replaceAll(/`([^`]+)`/g, "<code>$1</code>");
    text = text.replaceAll(
      /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
    );
    text = text.replaceAll("\n", "<br>");
    return text;
  });
  return htmlParts.join("");
}

function showToast(message, type) {
  let toast = document.getElementById("toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.remove("success", "error");
  if (type) toast.classList.add(type);
  toast.classList.add("show");
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.classList.remove("show");
  }, 1800);
}

async function copyTextToClipboard(text) {
  const value = String(text || "");
  if (!value) return false;
  try {
    if (navigator.clipboard && (window.isSecureContext || location.hostname === "localhost")) {
      await navigator.clipboard.writeText(value);
      return true;
    }
  } catch (e) {
  }

  try {
    const el = document.createElement("textarea");
    el.value = value;
    el.setAttribute("readonly", "readonly");
    el.style.position = "fixed";
    el.style.top = "-9999px";
    el.style.left = "-9999px";
    document.body.appendChild(el);
    el.select();
    el.setSelectionRange(0, el.value.length);
    const ok = document.execCommand("copy");
    document.body.removeChild(el);
    return ok;
  } catch (e) {
    return false;
  }
}

let globalChatMessages = null;

function renderChatHistory() {
  if (!dom.chatHistory) return;
  const messages = globalChatMessages || [];
  dom.chatHistory.innerHTML = "";
  messages.forEach((m) => {
    const wrapper = document.createElement("div");
    wrapper.className = `chat-msg ${m.role === "user" ? "user" : "assistant"}`;
    const meta = document.createElement("div");
    meta.className = "chat-meta";
    meta.textContent = m.role === "user" ? "你" : "AI";
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";
    if (m.loading) {
      bubble.innerHTML =
        '<span class="thinking">正在思考<span class="thinking-dots"><span>.</span><span>.</span><span>.</span></span></span>';
    } else {
      bubble.innerHTML = markdownToHtml(m.content || "");
    }
    const actions = document.createElement("div");
    actions.className = "chat-actions-row";
    const copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.className = "chat-copy";
    copyBtn.setAttribute("title", "复制");
    copyBtn.setAttribute("aria-label", "复制");
    copyBtn.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M9 9h10v11a1 1 0 0 1-1 1H10a1 1 0 0 1-1-1V9Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M6 15H5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>';
    const rawCopyText = String(m.content || "");
    copyBtn.disabled = Boolean(m.loading) || rawCopyText.trim().length === 0;
    copyBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const ok = await copyTextToClipboard(rawCopyText);
      showToast(ok ? "已复制" : "复制失败", ok ? "success" : "error");
    });
    actions.appendChild(copyBtn);
    wrapper.appendChild(meta);
    wrapper.appendChild(bubble);
    wrapper.appendChild(actions);
    dom.chatHistory.appendChild(wrapper);
  });
  dom.chatHistory.scrollTop = dom.chatHistory.scrollHeight;
}

function renderNovelList(items) {
  if (!dom.novelList) return;
  if (!items.length) {
    dom.novelList.classList.add("empty");
    dom.novelList.innerHTML = '<div class="empty-state">暂无小说，创建第一本吧</div>';
    return;
  }
  dom.novelList.classList.remove("empty");
  dom.novelList.innerHTML = items
    .map(
      (item) => `
      <div class="novel-card" data-id="${item.id}">
        <div class="novel-title">${item.title}</div>
        <div class="novel-meta">${item.created_at}</div>
      </div>
    `
    )
    .join("");
  dom.novelList.querySelectorAll(".novel-card").forEach((card) => {
    card.addEventListener("click", () => {
      const id = card.getAttribute("data-id");
      if (id) {
        window.location.href = `/novel/${id}`;
      }
    });
  });
}

async function initHome() {
  if (!dom.novelList || !dom.createBtn || !dom.titleInput) return;
  const list = await api.listNovels();
  renderNovelList(list);

  dom.createBtn.addEventListener("click", async () => {
    const title = dom.titleInput.value.trim();
    if (!title) return;
    dom.createBtn.disabled = true;
    try {
      const novel = await api.createNovel(title);
      dom.titleInput.value = "";
      const updated = await api.listNovels();
      renderNovelList(updated);
      window.location.href = `/novel/${novel.id}`;
    } finally {
      dom.createBtn.disabled = false;
    }
  });
}

async function initNovel() {
  const body = document.body;
  const novelId = body.getAttribute("data-novel-id");
  if (!novelId) return;

  const ensureOptimizeModal = () => {
    if (dom.optimizeModal && dom.optimizePrompt && dom.optimizeResult) {
      return;
    }
    const existing = document.getElementById("optimize-modal");
    if (!existing) {
      const wrapper = document.createElement("div");
      wrapper.innerHTML = `
        <div id="optimize-modal" class="modal">
          <div class="modal-content modal-split">
            <button id="optimize-close" class="modal-close-x" type="button" aria-label="关闭" title="关闭">
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M7 7l10 10M17 7L7 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
              </svg>
            </button>
            <div class="modal-left">
              <div class="modal-header">
                <div>
                  <div class="modal-title">AI 优化</div>
                  <div class="modal-sub">补充提示词与要求</div>
                </div>
              </div>
              <div class="modal-body">
                <label class="modal-label" for="optimize-prompt">提示词</label>
                <textarea id="optimize-prompt" rows="4" placeholder="输入优化方向、要求、风格等"></textarea>
                <label class="modal-label" for="optimize-result">AI 结果</label>
                <textarea id="optimize-result" rows="10" placeholder="等待生成结果" readonly></textarea>
              </div>
              <div class="modal-actions">
                <button id="optimize-submit">生成优化</button>
                <button id="optimize-apply" class="ghost">保留</button>
                <button id="optimize-revert" class="ghost">撤销</button>
              </div>
            </div>

            <div class="modal-right">
              <div class="chat-panel">
                <div class="chat-title">对话</div>
                <div id="chat-history" class="chat-history"></div>
                <div class="chat-footer">
                  <textarea id="chat-input" rows="3" placeholder="输入你的问题"></textarea>
                  <div class="chat-actions">
                    <label class="chat-toggle">
                      <input id="chat-search" type="checkbox" />
                      搜索
                    </label>
                    <button id="chat-send">发送</button>
                    <button id="chat-clear" class="ghost">清空</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(wrapper.firstElementChild);
    }
    dom.optimizeModal = document.getElementById("optimize-modal");
    dom.optimizePrompt = document.getElementById("optimize-prompt");
    dom.optimizeResult = document.getElementById("optimize-result");
    dom.optimizeSubmit = document.getElementById("optimize-submit");
    dom.optimizeApply = document.getElementById("optimize-apply");
    dom.optimizeRevert = document.getElementById("optimize-revert");
    dom.optimizeClose = document.getElementById("optimize-close");
    dom.chatHistory = document.getElementById("chat-history");
    dom.chatInput = document.getElementById("chat-input");
    dom.chatSearch = document.getElementById("chat-search");
    dom.chatSend = document.getElementById("chat-send");
    dom.chatClear = document.getElementById("chat-clear");
  };

  ensureOptimizeModal();

  if (globalChatMessages === null) {
    try {
      const history = await api.getChatHistory();
      globalChatMessages = Array.isArray(history.messages) ? history.messages : [];
    } catch (e) {
      globalChatMessages = [];
    }
  }
  renderChatHistory();

  const appendChatMessage = (role, content, extra) => {
    if (!globalChatMessages) globalChatMessages = [];
    globalChatMessages.push({ role, content, ...(extra || {}) });
    if (globalChatMessages.length > 60) {
      globalChatMessages = globalChatMessages.slice(-60);
    }
    renderChatHistory();
  };

  const updateChatMessage = (id, updates) => {
    if (!globalChatMessages) return;
    const idx = globalChatMessages.findIndex((m) => m.id === id);
    if (idx === -1) return;
    globalChatMessages[idx] = { ...globalChatMessages[idx], ...(updates || {}) };
    renderChatHistory();
  };

  if (dom.chatSend) {
    dom.chatSend.addEventListener("click", async () => {
      if (!dom.chatInput) return;
      const text = dom.chatInput.value.trim();
      if (!text) return;
      dom.chatSend.disabled = true;
      appendChatMessage("user", text);
      const pendingId = Date.now() + Math.random();
      appendChatMessage("assistant", "", { id: pendingId, loading: true });
      dom.chatInput.value = "";
      try {
        const useSearch = Boolean(dom.chatSearch && dom.chatSearch.checked);
        const res = await fetch("/api/chat/send_stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text, use_search: useSearch }),
        });
        if (!res.ok) {
          throw new Error("chat_failed");
        }
        if (!res.body) {
          throw new Error("chat_stream_unsupported");
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let assistantText = "";
        let scheduled = false;

        const scheduleRender = () => {
          if (scheduled) return;
          scheduled = true;
          requestAnimationFrame(() => {
            scheduled = false;
            updateChatMessage(pendingId, { loading: false, content: assistantText });
          });
        };

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          if (value) {
            assistantText += decoder.decode(value, { stream: true });
            scheduleRender();
          }
        }
        assistantText += decoder.decode();
        updateChatMessage(pendingId, { loading: false, content: assistantText });
      } catch (e) {
        updateChatMessage(pendingId, { loading: false, content: "发送失败，请稍后再试。" });
      } finally {
        dom.chatSend.disabled = false;
      }
    });
  }

  if (dom.chatInput) {
    dom.chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (dom.chatSend && !dom.chatSend.disabled) {
          dom.chatSend.click();
        }
      }
    });
  }

  if (dom.chatClear) {
    dom.chatClear.addEventListener("click", async () => {
      dom.chatClear.disabled = true;
      try {
        await api.clearChat();
        globalChatMessages = [];
        renderChatHistory();
      } finally {
        dom.chatClear.disabled = false;
      }
    });
  }

  const data = await api.getNovel(novelId);
  const titleNode = document.getElementById("novel-title");
  if (titleNode) {
    titleNode.textContent = data.novel.title || "故事背景";
  }
  const setValueIfExists = (id, value) => {
    const node = document.getElementById(id);
    if (node) node.value = value || "";
  };
  setValueIfExists("background", data.story ? data.story.background : "");
  setValueIfExists("mainline", data.story ? data.story.mainline : "");
  setValueIfExists("darkline", data.story ? data.story.darkline : "");
  setValueIfExists("style", data.advanced ? data.advanced.style : "");
  setValueIfExists("core_design", data.advanced ? data.advanced.core_design : "");
  setValueIfExists("reversal", data.advanced ? data.advanced.reversal : "");
  setValueIfExists("highlights", data.advanced ? data.advanced.highlights : "");

  const menuItems = document.querySelectorAll(".menu-item");
  const groups = document.querySelectorAll(".section-group");
  let activeSection = "story";

  const sectionMeta = {
    story: { title: "故事背景", subtitle: "整理世界观与主线脉络" },
    advanced: { title: "高级设计", subtitle: "强化风格与反转结构" },
  };

  const setActiveSection = (name) => {
    activeSection = name;
    menuItems.forEach((item) => {
      item.classList.toggle("active", item.getAttribute("data-section") === name);
    });
    groups.forEach((group) => {
      group.classList.toggle("active", group.getAttribute("data-section") === name);
    });
    if (titleNode) {
      titleNode.textContent = sectionMeta[name].title;
    }
    const subNode = document.querySelector(".content-header .sub");
    if (subNode) {
      subNode.textContent = sectionMeta[name].subtitle;
    }
  };

  menuItems.forEach((item) => {
    item.addEventListener("click", () => {
      const name = item.getAttribute("data-section");
      if (name) {
        setActiveSection(name);
        setStatus("");
      }
    });
  });

  let currentTarget = null;
  let currentField = "";
  let originalSnapshot = "";
  let candidateText = "";
  let loadingTimer = null;

  const defaultInstructionByField = {
    background: "在不改变设定的前提下，优化表达更清晰、更有画面感、更有张力。",
    mainline: "梳理事件因果与节奏，突出目标、阻力与转折点，表达更紧凑清晰。",
    darkline: "增强伏笔与信息差设计，保证逻辑自洽，表达更具悬念。",
    style: "提炼风格关键词与叙事气质，给出更明确可执行的写作指引。",
    core_design: "明确核心谜题、关键线索与解谜路径，保证逻辑自洽。",
    reversal: "设计反转的触发点与信息披露顺序，保证反转合理且冲击力强。",
    highlights: "提炼差异化卖点与读者记忆点，语言更有吸引力。",
  };

  const openOptimizeModal = (target, field) => {
    if (!dom.optimizeModal || !dom.optimizePrompt || !dom.optimizeResult) return;
    currentTarget = target;
    currentField = field;
    originalSnapshot = target.value;
    candidateText = "";
    dom.optimizePrompt.value = defaultInstructionByField[field] || "";
    dom.optimizeResult.value = "";
    dom.optimizeApply.disabled = true;
    dom.optimizeRevert.disabled = true;
    dom.optimizeModal.classList.add("active");
    dom.optimizePrompt.focus();
  };

  const closeOptimizeModal = () => {
    if (!dom.optimizeModal) return;
    dom.optimizeModal.classList.remove("active");
    if (loadingTimer) {
      clearInterval(loadingTimer);
      loadingTimer = null;
    }
  };

  if (dom.optimizeClose) {
    dom.optimizeClose.addEventListener("click", () => {
      closeOptimizeModal();
    });
  }

  if (dom.optimizeApply) {
    dom.optimizeApply.addEventListener("click", () => {
      if (currentTarget && candidateText) {
        currentTarget.value = candidateText;
      }
      setStatus("已保留 AI 结果");
      closeOptimizeModal();
    });
  }

  if (dom.optimizeRevert) {
    dom.optimizeRevert.addEventListener("click", () => {
      setStatus("已撤销 AI 结果");
      closeOptimizeModal();
    });
  }

  if (dom.optimizeSubmit) {
    dom.optimizeSubmit.addEventListener("click", async () => {
      if (!currentTarget) return;
      dom.optimizeSubmit.disabled = true;
      setStatus("AI 优化中...");
      try {
        if (dom.optimizeResult) {
          dom.optimizeResult.value = "生成中";
        }
        if (loadingTimer) {
          clearInterval(loadingTimer);
          loadingTimer = null;
        }
        let dotCount = 0;
        loadingTimer = setInterval(() => {
          dotCount = (dotCount + 1) % 4;
          const dots = ".".repeat(dotCount);
          if (dom.optimizeResult) {
            dom.optimizeResult.value = `生成中${dots}`;
          }
        }, 350);

        const result = await api.optimize({
          original: originalSnapshot,
          instruction: dom.optimizePrompt ? dom.optimizePrompt.value : "",
          field: currentField,
        });
        const text = result.text || "";
        candidateText = text;
        if (loadingTimer) {
          clearInterval(loadingTimer);
          loadingTimer = null;
        }
        if (dom.optimizeResult) dom.optimizeResult.value = text;
        if (dom.optimizeApply) dom.optimizeApply.disabled = false;
        if (dom.optimizeRevert) dom.optimizeRevert.disabled = false;
        setStatus("AI 优化完成，可保留或撤销");
      } catch (e) {
        if (loadingTimer) {
          clearInterval(loadingTimer);
          loadingTimer = null;
        }
        const message = String(e && e.message ? e.message : e);
        if (dom.optimizeResult) dom.optimizeResult.value = `生成失败：${message}`;
        setStatus("AI 优化失败");
      } finally {
        dom.optimizeSubmit.disabled = false;
      }
    });
  }

  const fieldToTextareaId = {
    background: "background",
    mainline: "mainline",
    darkline: "darkline",
    style: "style",
    core_design: "core_design",
    reversal: "reversal",
    highlights: "highlights",
  };

  document.querySelectorAll("[data-optimize]").forEach((button) => {
    button.addEventListener("click", () => {
      const field = button.getAttribute("data-optimize");
      const textareaId = fieldToTextareaId[field];
      const target = textareaId ? document.getElementById(textareaId) : null;
      if (field && target) {
        openOptimizeModal(target, field);
      } else {
        setStatus("找不到要优化的输入框");
      }
    });
  });

  if (dom.saveBtn) {
    dom.saveBtn.addEventListener("click", async () => {
      dom.saveBtn.disabled = true;
      const originalText = dom.saveBtn.textContent;
      dom.saveBtn.textContent = "保存中...";
      dom.saveBtn.classList.add("btn-loading");
      setStatus("保存中...");
      try {
        if (activeSection === "story") {
          const background = document.getElementById("background");
          const mainline = document.getElementById("mainline");
          const darkline = document.getElementById("darkline");
          await api.saveStory(novelId, {
            background: background ? background.value : "",
            mainline: mainline ? mainline.value : "",
            darkline: darkline ? darkline.value : "",
          });
        } else {
          const style = document.getElementById("style");
          const coreDesign = document.getElementById("core_design");
          const reversal = document.getElementById("reversal");
          const highlights = document.getElementById("highlights");
          await api.saveAdvanced(novelId, {
            style: style ? style.value : "",
            core_design: coreDesign ? coreDesign.value : "",
            reversal: reversal ? reversal.value : "",
            highlights: highlights ? highlights.value : "",
          });
        }
        setStatus("已保存");
        showToast("保存成功", "success");
        dom.saveBtn.textContent = "已保存";
        setTimeout(() => {
          if (dom.saveBtn) dom.saveBtn.textContent = originalText;
        }, 900);
      } catch (e) {
        setStatus("保存失败");
        showToast("保存失败", "error");
      } finally {
        dom.saveBtn.disabled = false;
        dom.saveBtn.classList.remove("btn-loading");
      }
    });
  }

  setActiveSection(activeSection);
}

const page = document.body.getAttribute("data-page");
if (page === "home") {
  initHome();
}
if (page === "novel") {
  initNovel();
}
