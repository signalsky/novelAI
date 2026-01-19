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
  async optimize(text, field) {
    const res = await fetch("/api/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, field }),
    });
    if (!res.ok) {
      throw new Error("optimize_failed");
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
};

function setStatus(message) {
  if (!dom.status) return;
  dom.status.textContent = message;
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
  const background = document.getElementById("background");
  const mainline = document.getElementById("mainline");
  const darkline = document.getElementById("darkline");
  const style = document.getElementById("style");
  const coreDesign = document.getElementById("core_design");
  const reversal = document.getElementById("reversal");
  const highlights = document.getElementById("highlights");
  if (!background || !mainline || !darkline || !style || !coreDesign || !reversal || !highlights) {
    return;
  }

  const data = await api.getNovel(novelId);
  const titleNode = document.getElementById("novel-title");
  if (titleNode) {
    titleNode.textContent = data.novel.title || "故事背景";
  }
  background.value = data.story.background || "";
  mainline.value = data.story.mainline || "";
  darkline.value = data.story.darkline || "";
  style.value = data.advanced.style || "";
  coreDesign.value = data.advanced.core_design || "";
  reversal.value = data.advanced.reversal || "";
  highlights.value = data.advanced.highlights || "";

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

  document.querySelectorAll("[data-optimize]").forEach((button) => {
    button.addEventListener("click", async () => {
      const field = button.getAttribute("data-optimize");
      let target = background;
      if (field === "mainline") target = mainline;
      if (field === "darkline") target = darkline;
      if (field === "style") target = style;
      if (field === "core_design") target = coreDesign;
      if (field === "reversal") target = reversal;
      if (field === "highlights") target = highlights;
      button.disabled = true;
      try {
        const result = await api.optimize(target.value, field);
        target.value = result.text || "";
        setStatus("已完成 AI 优化");
      } finally {
        button.disabled = false;
      }
    });
  });

  if (dom.saveBtn) {
    dom.saveBtn.addEventListener("click", async () => {
      dom.saveBtn.disabled = true;
      setStatus("保存中...");
      try {
        if (activeSection === "story") {
          await api.saveStory(novelId, {
            background: background.value,
            mainline: mainline.value,
            darkline: darkline.value,
          });
        } else {
          await api.saveAdvanced(novelId, {
            style: style.value,
            core_design: coreDesign.value,
            reversal: reversal.value,
            highlights: highlights.value,
          });
        }
        setStatus("已保存");
      } finally {
        dom.saveBtn.disabled = false;
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
