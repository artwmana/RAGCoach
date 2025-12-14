const uploadForm = document.getElementById("uploadForm");
const uploadStatus = document.getElementById("uploadStatus");
const searchForm = document.getElementById("searchForm");
const questionField = document.getElementById("question");
const topK = document.getElementById("topK");
const topKValue = document.getElementById("topKValue");
const resultsBlock = document.getElementById("results");
const useContextBtn = document.getElementById("useContext");
const gradeForm = document.getElementById("gradeForm");
const gradeQuestion = document.getElementById("gradeQuestion");
const studentAnswer = document.getElementById("studentAnswer");
const contextField = document.getElementById("context");
const gradeResult = document.getElementById("gradeResult");
const promptForm = document.getElementById("promptForm");
const promptField = document.getElementById("prompt");
const promptResult = document.getElementById("promptResult");
const toast = document.getElementById("toast");

let lastContext = "";

const showToast = (message, tone = "info") => {
  if (!toast) return;
  toast.textContent = message;
  toast.style.borderLeftColor =
    tone === "error" ? "var(--danger)" : tone === "success" ? "var(--accent)" : "var(--accent-2)";
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3200);
};

const fetchJson = async (url, options) => {
  const res = await fetch(url, options);
  const isJson = (res.headers.get("content-type") || "").includes("application/json");
  const data = isJson ? await res.json() : await res.text();
  if (!res.ok) {
    const detail = (data && data.detail) || data.message || data;
    throw new Error(detail || `Ошибка: ${res.status}`);
  }
  return data;
};

const setLoading = (button, isLoading, label) => {
  if (!button) return;
  if (isLoading) {
    button.dataset.label = button.textContent;
    button.textContent = label || "Загружается...";
    button.disabled = true;
  } else {
    button.textContent = button.dataset.label || "Готово";
    button.disabled = false;
  }
};

if (topK && topKValue) {
  topK.addEventListener("input", () => {
    topKValue.textContent = topK.value;
  });
}

if (uploadForm) {
  uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fileInput = uploadForm.querySelector('input[type="file"]');
    const submitBtn = uploadForm.querySelector("button[type=submit]");
    if (!fileInput.files.length) {
      showToast("Выберите PDF-файл", "error");
      return;
    }
    const formData = new FormData(uploadForm);
    setLoading(submitBtn, true, "Индексируем...");
    uploadStatus.textContent = "Загрузка...";
    try {
      const data = await fetchJson("/api/upload_pdf", {
        method: "POST",
        body: formData,
      });
      uploadStatus.textContent = `✅ Добавлено чанков: ${data.inserted}\nКоллекция: ${data.collection}\nJSON: ${data.json_path}`;
      showToast("Лекция загружена и проиндексирована", "success");
    } catch (err) {
      uploadStatus.textContent = `Ошибка: ${err.message}`;
      showToast(err.message, "error");
    } finally {
      setLoading(submitBtn, false);
    }
  });
}

const renderResults = (items = []) => {
  if (!resultsBlock) return;
  resultsBlock.innerHTML = "";
  if (!items.length) {
    resultsBlock.innerHTML = '<p class="hint">Ничего не найдено</p>';
    lastContext = "";
    return;
  }

  lastContext = items
    .map((hit) => hit?.payload?.text || "")
    .filter(Boolean)
    .join("\n\n");

  items.forEach((hit, idx) => {
    const wrapper = document.createElement("div");
    wrapper.className = "result";
    const payload = hit.payload || {};
    wrapper.innerHTML = `
      <div class="result-meta">
        <span class="score">#${idx + 1} · ${hit.score?.toFixed?.(3) ?? hit.score}</span>
        <span class="payload">src: ${payload.source || payload.filename || "–"}</span>
        <span class="payload">page: ${payload.page || "?"}</span>
        <span class="payload">chunk: ${payload.chunk_id ?? "?"}</span>
      </div>
      <div>${(payload.text || "").slice(0, 800)}</div>
    `;
    resultsBlock.appendChild(wrapper);
  });
};

if (searchForm) {
  searchForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = searchForm.querySelector("button[type=submit]");
    const question = questionField.value.trim();
    if (!question) {
      showToast("Введите вопрос", "error");
      return;
    }
    setLoading(submitBtn, true, "Ищем...");
    resultsBlock.innerHTML = "";
    try {
      const data = await fetchJson("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, top_k: Number(topK.value) }),
      });
      renderResults(data.results || []);
      if (gradeQuestion && !gradeQuestion.value.trim()) {
        gradeQuestion.value = data.question || question;
      }
      showToast("Поиск завершён", "success");
    } catch (err) {
      resultsBlock.innerHTML = `<p class="hint">Ошибка: ${err.message}</p>`;
      showToast(err.message, "error");
    } finally {
      setLoading(submitBtn, false);
    }
  });
}

if (useContextBtn) {
  useContextBtn.addEventListener("click", () => {
    if (!lastContext) {
      showToast("Сначала выполните поиск", "error");
      return;
    }
    if (contextField) {
      contextField.value = lastContext;
      showToast("Контекст добавлен в форму оценки", "success");
    }
  });
}

if (gradeForm) {
  gradeForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = gradeForm.querySelector("button[type=submit]");
    const payload = {
      question: gradeQuestion.value.trim(),
      student_answer: studentAnswer.value.trim(),
      lecture_snippet: contextField.value.trim() || null,
    };
    if (!payload.question || !payload.student_answer) {
      showToast("Заполните вопрос и ответ", "error");
      return;
    }
    setLoading(submitBtn, true, "Оцениваем...");
    gradeResult.textContent = "";
    try {
      const data = await fetchJson("/api/grade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      gradeResult.textContent = data.result || "Ответ пуст";
      showToast("Оценка готова", "success");
    } catch (err) {
      gradeResult.textContent = `Ошибка: ${err.message}`;
      showToast(err.message, "error");
    } finally {
      setLoading(submitBtn, false);
    }
  });
}

if (promptForm) {
  promptForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = promptForm.querySelector("button[type=submit]");
    const prompt = promptField.value.trim();
    if (!prompt) {
      showToast("Введите промпт", "error");
      return;
    }
    setLoading(submitBtn, true, "Отправляем...");
    promptResult.textContent = "";
    try {
      const data = await fetchJson("/api/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      promptResult.textContent = data.result || "Ответ пуст";
      showToast("Ответ получен", "success");
    } catch (err) {
      promptResult.textContent = `Ошибка: ${err.message}`;
      showToast(err.message, "error");
    } finally {
      setLoading(submitBtn, false);
    }
  });
}
