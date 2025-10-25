// Anki单词卡片生成器 - 前端JavaScript

// 全局变量
let selectedWords = [];
let generatedCards = [];
let currentConfig = {};

// 工具函数
function showLoading(button, loading = true) {
    if (loading) {
        button.disabled = true;
        button.innerHTML = '<span class="loading"></span> 处理中...';
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText || button.innerHTML;
    }
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const container = document.querySelector('main .container');
    container.insertBefore(alertDiv, container.firstChild);

    // 3秒后自动关闭
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

function updateProgressBar(current, total, text = '') {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const progressContainer = document.getElementById('progress-container');

    if (total > 0) {
        const percentage = Math.round((current / total) * 100);
        progressBar.style.width = `${percentage}%`;
        progressBar.textContent = `${percentage}%`;
        progressText.textContent = text || `${current}/${total}`;
        progressContainer.style.display = 'block';
    } else {
        progressContainer.style.display = 'none';
    }
}

// 初始化应用
function initializeApp() {
    setupEventListeners();
    loadCategoriesAndDifficulties();
}

// 设置事件监听器
function setupEventListeners() {
    // 选择方式变化
    document.getElementById('selection-type').addEventListener('change', function() {
        const categoryDifficulty = document.getElementById('category-difficulty');
        categoryDifficulty.innerHTML = '<option value="">全部</option>';

        if (this.value === 'category') {
            loadCategories();
        } else if (this.value === 'difficulty') {
            loadDifficulties();
        }
    });

    // 加载内置单词
    document.getElementById('load-builtin-words').addEventListener('click', loadBuiltinWords);

    // 文件上传
    document.getElementById('browse-btn').addEventListener('click', () => {
        document.getElementById('file-input').click();
    });

    document.getElementById('file-input').addEventListener('change', handleFileSelect);

    // 拖拽上传
    const uploadArea = document.getElementById('upload-area');
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleFileDrop);
    uploadArea.addEventListener('click', () => {
        document.getElementById('file-input').click();
    });

    // 手动输入
    document.getElementById('manual-words').addEventListener('input', handleManualInput);

    // 单词列表操作
    document.getElementById('clear-list').addEventListener('click', clearWordList);
    document.getElementById('preview-btn').addEventListener('click', previewGeneration);

    // 生成控制
    document.getElementById('generate-btn').addEventListener('click', startGeneration);
    document.getElementById('confirm-generate').addEventListener('click', confirmGeneration);

    // 导出控制
    document.getElementById('export-csv').addEventListener('click', () => exportCards('csv'));
    document.getElementById('export-apkg').addEventListener('click', () => exportCards('apkg'));
    document.getElementById('export-study').addEventListener('click', () => exportCards('study'));
}

// 加载配置信息
function loadConfig() {
    fetch('/api/config')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentConfig = data.data;
                displayConfig();
            } else {
                showAlert('加载配置信息失败: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            showAlert('获取配置信息失败: ' + error, 'danger');
        });
}

function displayConfig() {
    document.getElementById('provider-display').textContent =
        currentConfig.llm_config.provider.toUpperCase();
    document.getElementById('model-display').textContent =
        currentConfig.llm_config.model;
    document.getElementById('examples-count').textContent =
        currentConfig.generation_rules.example_count;
    document.getElementById('synonyms-count').textContent =
        currentConfig.generation_rules.synonym_count;
    document.getElementById('tip-types').textContent =
        currentConfig.generation_rules.tip_types.join(', ');
}

// 加载统计信息
function loadStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 可以在页面上显示统计信息
                console.log('统计信息:', data.data);
            }
        })
        .catch(error => {
            console.error('加载统计信息失败:', error);
        });
}

// 加载分类
function loadCategories() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const select = document.getElementById('category-difficulty');
                const categories = Object.keys(data.data.category_distribution);

                categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category;
                    option.textContent = category;
                    select.appendChild(option);
                });
            }
        });
}

// 加载难度
function loadDifficulties() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const select = document.getElementById('category-difficulty');
                const difficulties = Object.keys(data.data.difficulty_distribution);

                difficulties.forEach(difficulty => {
                    const option = document.createElement('option');
                    option.value = difficulty;
                    option.textContent = difficulty;
                    select.appendChild(option);
                });
            }
        });
}

// 加载分类和难度选项
function loadCategoriesAndDifficulties() {
    // 预加载分类和难度选项
    const categories = ['情感', '能力', '状态', '程度', '概念', '教育', '行为', '事件', '成就'];
    const difficulties = ['easy', 'medium', 'hard', 'common', 'less_common'];

    const select = document.getElementById('category-difficulty');

    if (document.getElementById('selection-type').value === 'category') {
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            select.appendChild(option);
        });
    } else if (document.getElementById('selection-type').value === 'difficulty') {
        difficulties.forEach(difficulty => {
            const option = document.createElement('option');
            option.value = difficulty;
            option.textContent = difficulty;
            select.appendChild(option);
        });
    }
}

// 加载内置单词
function loadBuiltinWords() {
    const selectionType = document.getElementById('selection-type').value;
    const count = parseInt(document.getElementById('word-count').value);
    const categoryDifficulty = document.getElementById('category-difficulty').value;

    const url = new URL('/api/words/builtin', window.location.origin);
    url.searchParams.append('count', count);
    url.searchParams.append('random', selectionType === 'random');

    if (selectionType === 'category' && categoryDifficulty) {
        url.searchParams.append('category', categoryDifficulty);
    } else if (selectionType === 'difficulty' && categoryDifficulty) {
        url.searchParams.append('difficulty', categoryDifficulty);
    }

    const button = document.getElementById('load-builtin-words');
    showLoading(button, true);

    fetch(url.toString())
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                selectedWords = data.data.words;
                updateWordList();
                showAlert(`成功加载 ${data.data.total} 个单词`, 'success');
            } else {
                showAlert('加载单词失败: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            showAlert('加载单词失败: ' + error, 'danger');
        })
        .finally(() => {
            showLoading(button, false);
        });
}

// 处理文件选择
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        uploadFile(file);
    }
}

// 处理拖拽
function handleDragOver(event) {
    event.preventDefault();
    event.currentTarget.classList.add('dragover');
}

function handleDragLeave(event) {
    event.currentTarget.classList.remove('dragover');
}

function handleFileDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('dragover');

    const files = event.dataTransfer.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
}

// 上传文件
function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const uploadArea = document.getElementById('upload-area');
    uploadArea.innerHTML = '<span class="loading"></span> 上传中...';

    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showFilePreview(data.data);
            showAlert('文件上传成功', 'success');
        } else {
            showAlert('文件上传失败: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        showAlert('文件上传失败: ' + error, 'danger');
    })
    .finally(() => {
        uploadArea.innerHTML = '<i class="bi bi-cloud-upload fs-1 text-muted"></i>' +
                           '<p class="text-muted mt-2 mb-3">拖拽文件到此处或点击选择</p>' +
                           '<button class="btn btn-outline-primary" id="browse-btn">' +
                           '<i class="bi bi-folder2-open"></i> 浏览文件</button>' +
                           '<div class="form-text text-start mt-2">支持格式：TXT, CSV, JSON（最大16MB）</div>';

        // 重新绑定事件
        document.getElementById('browse-btn').addEventListener('click', () => {
            document.getElementById('file-input').click();
        });
    });
}

// 显示文件预览
function showFilePreview(fileData) {
    const preview = document.getElementById('file-preview');
    const previewData = fileData.preview;

    let previewHtml = `
        <div class="alert alert-info">
            <i class="bi bi-file-earmark-text"></i>
            <strong>文件:</strong> ${fileData.filename}<br>
            <strong>格式:</strong> ${previewData.format}<br>
            <strong>预估单词数:</strong> ${previewData.estimated_words || '未知'}
        </div>
    `;

    if (previewData.preview_lines) {
        previewHtml += `
            <div class="mt-2">
                <strong>预览前几行:</strong>
                <div class="bg-light p-2 rounded mt-1">
                    ${previewData.preview_lines.slice(0, 5).map(line => `<div>${line}</div>`).join('')}
                </div>
            </div>
        `;
    }

    if (previewData.preview_rows) {
        previewHtml += `
            <div class="mt-2">
                <strong>数据预览:</strong>
                <div class="bg-light p-2 rounded mt-1">
                    <small>列: ${previewData.columns.join(', ')}</small>
                </div>
            </div>
        `;
    }

    preview.innerHTML = previewHtml;
    preview.style.display = 'block';

    // 添加确认按钮
    const confirmBtn = document.createElement('button');
    confirmBtn.className = 'btn btn-primary mt-2';
    confirmBtn.innerHTML = '<i class="bi bi-check-circle"></i> 使用此词库';
    confirmBtn.addEventListener('click', () => {
        selectedWords = extractWordsFromFile(fileData);
        updateWordList();
    });
    preview.appendChild(confirmBtn);
}

// 从文件数据提取单词
function extractWordsFromFile(fileData) {
    // 这里简化处理，实际应该从预览数据中提取
    return ['sample', 'words', 'from', 'file']; // 示例，需要实现真正的提取逻辑
}

// 处理手动输入
function handleManualInput(event) {
    const text = event.target.value.trim();
    if (text) {
        const words = text.split('\n')
            .map(word => word.trim())
            .filter(word => word && /^[a-zA-Z]+$/.test(word))
            .slice(0, 50); // 最多50个单词

        selectedWords = words;
        updateWordList();
    }
}

// 更新单词列表
function updateWordList() {
    const wordList = document.getElementById('word-list');
    const countElement = document.getElementById('selected-count');

    if (selectedWords.length === 0) {
        wordList.innerHTML = '<p class="text-muted text-center">请先选择单词</p>';
    } else {
        wordList.innerHTML = selectedWords
            .map(word => `<span class="word-item">${word}</span>`)
            .join('');
    }

    countElement.textContent = selectedWords.length;
}

// 清空单词列表
function clearWordList() {
    selectedWords = [];
    updateWordList();
    showAlert('单词列表已清空', 'info');
}

// 预览生成
function previewGeneration() {
    if (selectedWords.length === 0) {
        showAlert('请先选择要生成的单词', 'warning');
        return;
    }

    const previewWords = selectedWords.slice(0, 3); // 预览前3个

    fetch('/api/words/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            words: previewWords,
            preview: true
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showPreviewModal(data.preview);
        } else {
            showAlert('预览失败: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        showAlert('预览失败: ' + error, 'danger');
    });
}

// 显示预览模态框
function showPreviewModal(previewData) {
    const modal = document.getElementById('preview-modal');
    const content = document.getElementById('preview-content');

    let html = '';
    previewData.results.forEach(result => {
        if (result.success) {
            const card = result.preview;
            html += `
                <div class="generated-card">
                    <div class="word-title">${result.word}</div>
                    <div class="phonetic">${card.phonetic}</div>
                    <div class="meaning">${card.meaning}</div>
                    <div class="memory-tip">
                        <strong>${card.memory_tip.type}:</strong> ${card.memory_tip.content}
                    </div>
                    <div class="examples">
                        <strong>例句:</strong>
                        ${card.examples.slice(0, 2).map(ex => `
                            <div class="example">${ex}</div>
                        `).join('')}
                    </div>
                </div>
            `;
        } else {
            html += `
                <div class="alert alert-warning">
                    <strong>${result.word}:</strong> ${result.error}
                </div>
            `;
        }
    });

    content.innerHTML = html;

    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
}

// 确认生成
function confirmGeneration() {
    const modal = document.getElementById('preview-modal');
    const modalInstance = bootstrap.Modal.getInstance(modal);
    modalInstance.hide();

    startGeneration();
}

// 开始生成
function startGeneration() {
    if (selectedWords.length === 0) {
        showAlert('请先选择要生成的单词', 'warning');
        return;
    }

    // 显示进度
    updateProgressBar(0, selectedWords.length);

    const generateBtn = document.getElementById('generate-btn');
    showLoading(generateBtn, true);

    fetch('/api/words/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            words: selectedWords,
            preview: false
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const taskId = data.task_id;
            monitorGeneration(taskId);
        } else {
            showAlert('生成失败: ' + data.error, 'danger');
            showLoading(generateBtn, false);
        }
    })
    .catch(error => {
        showAlert('生成失败: ' + error, 'danger');
        showLoading(generateBtn, false);
    });
}

// 监控生成进度（简化版本，实际应该用WebSocket或轮询）
function monitorGeneration(taskId) {
    // 模拟生成过程
    let current = 0;
    const total = selectedWords.length;
    const interval = setInterval(() => {
        current++;
        updateProgressBar(current, total);

        if (current >= total) {
            clearInterval(interval);
            completeGeneration();
        }
    }, 1000); // 每秒更新一次进度
}

// 完成生成
function completeGeneration() {
    // 模拟生成结果
    const successCount = Math.floor(selectedWords.length * 0.9); // 假设90%成功率
    const failedCount = selectedWords.length - successCount;

    // 显示结果
    document.getElementById('success-count').textContent = successCount;
    document.getElementById('failed-count').textContent = failedCount;
    document.getElementById('results-card').style.display = 'block';

    // 生成示例卡片数据（实际应该从服务器获取）
    generatedCards = generateSampleCards(successCount);
    displayGeneratedCards();

    // 重置按钮
    const generateBtn = document.getElementById('generate-btn');
    showLoading(generateBtn, false);

    showAlert(`生成完成！成功 ${successCount} 个，失败 ${failedCount} 个`, 'success');
}

// 生成示例卡片数据
function generateSampleCards(count) {
    const sampleCards = [];
    for (let i = 0; i < Math.min(count, selectedWords.length); i++) {
        sampleCards.push({
            word: selectedWords[i],
            phonetic: '/ˈwɜːd/',
            part_of_speech: 'n.',
            meaning: '单词',
            memory_tip: {
                type: '谐音法',
                content: '记忆技巧示例'
            },
            examples: ['This is an example sentence.', 'Another example sentence.'],
            synonyms: ['synonym1', 'synonym2'],
            confusables: ['confusable1']
        });
    }
    return sampleCards;
}

// 显示生成的卡片
function displayGeneratedCards() {
    const container = document.getElementById('generated-cards');

    if (generatedCards.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">暂无生成的卡片</p>';
        return;
    }

    container.innerHTML = generatedCards.map(card => `
        <div class="generated-card">
            <div class="word-title">${card.word}</div>
            <div class="phonetic">${card.phonetic}</div>
            <div class="meaning">${card.meaning}</div>
            <div class="memory-tip">
                <strong>${card.memory_tip.type}:</strong> ${card.memory_tip.content}
            </div>
            <div class="examples">
                <strong>例句:</strong>
                ${card.examples.slice(0, 2).map(ex => `
                    <div class="example">${ex}</div>
                `).join('')}
            </div>
            <div class="synonyms">
                ${card.synonyms.map(syn => `<span class="tag">${syn}</span>`).join('')}
            </div>
            <div class="confusables">
                ${card.confusables.map(conf => `<span class="tag">${conf}</span>`).join('')}
            </div>
        </div>
    `).join('');
}

// 导出卡片
function exportCards(format) {
    if (generatedCards.length === 0) {
        showAlert('请先生成单词卡片', 'warning');
        return;
    }

    const exportData = {
        cards: generatedCards
    };

    fetch(`/api/export/${format}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(exportData)
    })
    .then(response => {
        if (response.ok) {
            // 获取文件名
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `anki_cards.${format === 'apkg' ? 'apkg' : 'csv'}`;

            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1].replace(/['"]/g, '');
                }
            }

            return response.blob().then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
            });
        } else {
            return response.json().then(data => {
                showAlert('导出失败: ' + (data.error || '未知错误'), 'danger');
            });
        }
    })
    .catch(error => {
        showAlert('导出失败: ' + error, 'danger');
    });
}