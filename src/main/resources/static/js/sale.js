/**
 * 세일 목록 로드 및 렌더링
 */

const pageSize = 20; 

// 출처 사이트 한글 매핑
const SOURCE_SITE_MAP = {
    'PPOMPPU': '뽐뿌',
    'RULIWEB': '루리웹',
    'FMKOREA': '에펨코리아',
    'QUASARZONE': '퀘이사존',
    'ARCALIVE': '아카라이브',
    'EOMISAE': '어미새'
};

/**
 * 세일 목록 로드
 */
async function loadSales(page = 0) {
    const loading = document.getElementById('loading');
    const saleList = document.getElementById('saleList');
    
    loading.style.display = 'block';
    saleList.style.display = 'none';
    
    try {
        // 필터 조건 수집
        const sourceSites = Array.from(
            document.querySelectorAll('input[type="checkbox"][id^="site-"]:checked')
        ).map(cb => cb.value);
        
        const keywordPc = document.getElementById('searchInputPc')?.value || '';
        const keywordMobile = document.getElementById('searchInputMobile')?.value || '';
        const keyword = keywordPc || keywordMobile;
        
        // 두 검색창 값 동기화
        if (document.getElementById('searchInputPc')) document.getElementById('searchInputPc').value = keyword;
        if (document.getElementById('searchInputMobile')) document.getElementById('searchInputMobile').value = keyword;

        // URL 파라미터 생성
        const params = new URLSearchParams({
            page: page,
            size: pageSize,
            sortBy: 'crawledAt'
        });

        if (keyword.trim() !== '') {
            params.append('keyword', keyword.trim());
        }
        sourceSites.forEach(site => params.append('sources', site));
        
        const queryString = params.toString();
        const response = await fetch(`/api/sales?${queryString}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        renderSaleCards(data.content);
        renderPagination(data); 
        
        document.getElementById('totalCount').textContent = data.totalElements || 0;
        
        // URL 업데이트
        const url = new URL(window.location);
        url.search = queryString; 
        window.history.pushState({ path: url.href }, '', url.href);
        
    } catch (error) {
        console.error('세일 목록 로드 실패:', error);
        saleList.innerHTML = `
            <div class="col-12 text-center py-5">
                <p class="text-danger">데이터를 불러올 수 없습니다.</p>
                <p class="text-muted">${error.message}</p>
            </div>
        `;
    } finally {
        loading.style.display = 'none';
        saleList.style.display = 'flex'; 
    }
}

/**
 * 세일 카드 렌더링
 */
function renderSaleCards(sales) {
    const saleList = document.getElementById('saleList');
    
    if (!sales || sales.length === 0) {
        saleList.innerHTML = `
            <div class="col-12 text-center py-5">
                <p class="text-muted">검색 결과가 없습니다.</p>
            </div>
        `;
        return;
    }
    
    const noImageSvg = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LXNpemU9IjE4IiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=';
    
    saleList.innerHTML = sales.map(sale => {
        const imageUrl = sale.imageUrl || noImageSvg;
        // 출처 사이트 한글 변환
        const sourceSiteKr = SOURCE_SITE_MAP[sale.sourceSite] || sale.sourceSite;
        
        return `
        <div class="col-6 col-md-6 col-lg-6"> 
            <div class="sale-card">
                <span class="sale-source-badge">${sourceSiteKr}</span>
                <a href="${sale.productUrl}" target="_blank">
                    <img src="${imageUrl}" 
                         class="sale-card-img" 
                         alt="${escapeHtml(sale.title)}" 
                         loading="lazy"
                         onerror="this.src='${noImageSvg}'">
                </a>
                <div class="sale-card-body">
                    <a href="${sale.productUrl}" target="_blank" class="text-decoration-none">
                        <h5 class="sale-title">${escapeHtml(sale.title)}</h5>
                    </a>
                    <div class="sale-price">${sale.price_str || ''}</div>
                    <div class="sale-store">
                        <i class="bi bi-shop"></i> ${escapeHtml(sale.storeName || '')}
                    </div>
                    <div class="sale-meta">
                        <span><i class="bi bi-heart"></i> ${formatNumber(sale.likeCount || 0)}</span>
                        <span><i class="bi bi-chat"></i> ${formatNumber(sale.commentCount || 0)}</span>
                        <span>${formatTimeHHMM(sale.crawledAt || sale.createdAt)}</span>
                    </div>
                </div>
            </div>
        </div>
        `;
    }).join('');
}

/**
 * 페이지네이션 렌더링 (맨앞/맨뒤 버튼 추가)
 */
function renderPagination(data) {
    const pagination = document.getElementById('pagination');
    const totalPages = data.totalPages || 0;
    const currentPage = data.page || 0;
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '<ul class="pagination justify-content-center">';
    
    // 맨 앞으로 버튼
    html += `
        <li class="page-item ${currentPage === 0 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="loadSales(0); return false;" title="첫 페이지">
                <i class="bi bi-chevron-double-left"></i>
            </a>
        </li>
    `;
    
    // 이전 버튼
    html += `
        <li class="page-item ${currentPage === 0 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="loadSales(${currentPage - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // 페이지 번호
    let startPage = Math.max(0, currentPage - 2);
    let endPage = Math.min(totalPages - 1, currentPage + 2);

    if (currentPage < 2) {
        endPage = Math.min(4, totalPages - 1);
    }
    if (currentPage > totalPages - 3) {
        startPage = Math.max(0, totalPages - 5);
    }
    
    if (startPage > 0) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="loadSales(0); return false;">1</a></li>`;
        if (startPage > 1) {
             html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="loadSales(${i}); return false;">
                    ${i + 1}
                </a>
            </li>
        `;
    }

    if (endPage < totalPages - 1) {
        if (endPage < totalPages - 2) {
             html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `<li class="page-item"><a class="page-link" href="#" onclick="loadSales(${totalPages - 1}); return false;">${totalPages}</a></li>`;
    }
    
    // 다음 버튼
    html += `
        <li class="page-item ${currentPage >= totalPages - 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="loadSales(${currentPage + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    // 맨 뒤로 버튼
    html += `
        <li class="page-item ${currentPage >= totalPages - 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="loadSales(${totalPages - 1}); return false;" title="마지막 페이지">
                <i class="bi bi-chevron-double-right"></i>
            </a>
        </li>
    `;
    
    html += '</ul>';
    pagination.innerHTML = html;
}

/**
 * 숫자 포맷
 */
function formatNumber(num) {
    return new Intl.NumberFormat('ko-KR').format(num || 0);
}

/**
 * 필터 적용
 */
function applyFilters() {
    syncSearchInputs();
    loadSales(0);
    
    // 모바일 Offcanvas 닫기
    const offcanvasElement = document.getElementById('filterOffcanvas');
    if (offcanvasElement) {
        const offcanvas = bootstrap.Offcanvas.getInstance(offcanvasElement);
        if (offcanvas) {
            offcanvas.hide();
        }
    }
}

/**
 * URL 파라미터로 필터/페이지 복원
 */
function loadSalesFromUrl() {
    const params = new URLSearchParams(window.location.search);
    
    const page = parseInt(params.get('page') || '0', 10);
    const keyword = params.get('keyword') || '';
    
    if (document.getElementById('searchInputPc')) {
        document.getElementById('searchInputPc').value = keyword;
    }
    if (document.getElementById('searchInputMobile')) {
        document.getElementById('searchInputMobile').value = keyword;
    }
    
    const sources = params.getAll('sources');
    if (sources.length > 0) {
        document.querySelectorAll('input[type="checkbox"][id^="site-"]').forEach(cb => {
            cb.checked = sources.includes(cb.value);
        });
    }
    
    loadSales(page);
}

/**
 * 검색창 동기화
 */
function syncSearchInputs() {
     const keywordPc = document.getElementById('searchInputPc');
     const keywordMobile = document.getElementById('searchInputMobile');
     if (!keywordPc || !keywordMobile) return;
     
     if (window.getComputedStyle(keywordPc).display !== 'none') {
         if(keywordMobile.value) keywordPc.value = keywordMobile.value;
     } 
     else if (window.getComputedStyle(keywordMobile).display !== 'none') {
         if(keywordPc.value) keywordMobile.value = keywordPc.value;
     }
}

/**
 * HH:mm 시간 포맷
 */
function formatTimeHHMM(dateString) {
    if (!dateString) return '';
    
    try {
        const date = new Date(dateString);
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${hours}:${minutes}`;
    } catch (e) {
        return '';
    }
}

/**
 * HTML 이스케이프
 */
function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}