/**
 * 세일 목록 로드 및 렌더링
 */

// 💡 [수정] 5. 모바일) 페이지 크기를 20으로 변경
const pageSize = 20; 

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
        
        // 💡 [수정] 주석 처리되었더라도, 값이 없는 경우 기본값 0 또는 10000000 사용
        const minPrice = document.getElementById('minPrice')?.value || 0;
        const maxPrice = document.getElementById('maxPrice')?.value || 10000000;
        const sortBy = document.getElementById('sortBy')?.value || 'latest';
        
        // 💡 [수정] 4. 모바일) PC와 모바일 검색창 값 동기화 및 수집
        const keywordPc = document.getElementById('searchInputPc')?.value || '';
        const keywordMobile = document.getElementById('searchInputMobile')?.value || '';
        const keyword = keywordPc || keywordMobile; // 둘 중 하나라도 값 있으면 사용
        
        // (UX 개선) 두 검색창 값을 동일하게 맞춤
        if (document.getElementById('searchInputPc')) document.getElementById('searchInputPc').value = keyword;
        if (document.getElementById('searchInputMobile')) document.getElementById('searchInputMobile').value = keyword;

        
        // URL 파라미터 생성
        const params = new URLSearchParams({
            page: page,
            size: pageSize,
            sortBy: sortBy,
            minPrice: minPrice,
            maxPrice: maxPrice
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
        // 💡 [수정] 3. 페이징) API 응답(data)을 renderPagination에 전달
        renderPagination(data); 
        
        document.getElementById('totalCount').textContent = data.totalElements || 0;
        
        // 💡 [수정] URL 업데이트 (페이지 새로고침 없음)
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
    
    const noImageSvg = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LXNpemU9IjE4IiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIj5ObyBJbWFnZTwvdGV4dD48L2RleHQ+PC9zdmc+';
    
    saleList.innerHTML = sales.map(sale => {
        const imageUrl = sale.imageUrl || noImageSvg;
        
        // 💡 [요청 5] 모바일 2열(col-6), PC/태블릿 2열(col-md-6, col-lg-6) 적용
        return `
        <div class="col-6 col-md-6 col-lg-6"> 
            <div class="sale-card">
                <span class="sale-source-badge">${sale.sourceSite || '알 수 없음'}</span>
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
                    <div class="sale-price">${sale.price_str || '가격 문의'}</div>
                    <div class="sale-store">
                        <i class="bi bi-shop"></i> ${escapeHtml(sale.storeName || '정보 없음')}
                    </div>
                    <div class="sale-meta">
                        <span><i class="bi bi-heart"></i> ${formatNumber(sale.likeCount || 0)}</span>
                        <span><i class="bi bi-chat"></i> ${formatNumber(sale.commentCount || 0)}</span>
                        <span>${formatDate(sale.createdAt)}</span>
                    </div>
                </div>
            </div>
        </div>
        `;
    }).join('');
}

/**
 * 💡 [수정] 3. 페이징) 페이지네이션 렌더링 (PC/모바일 페이징 버그 수정)
 */
function renderPagination(data) {
    const pagination = document.getElementById('pagination');
    const totalPages = data.totalPages || 0;
    // 💡 [수정] 3. 페이징) data.number -> data.page
    const currentPage = data.page || 0; // 0부터 시작하는 현재 페이지 번호
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '<ul class="pagination justify-content-center">';
    
    // 이전 버튼
    html += `
        <li class="page-item ${currentPage === 0 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="loadSales(${currentPage - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // 💡 [수정] 페이지 번호 로직 (슬라이딩 윈도우 + 첫/끝 페이지)
    let startPage = Math.max(0, currentPage - 2);
    let endPage = Math.min(totalPages - 1, currentPage + 2);

    // 5개 페이지를 항상 표시하도록 조정 (가능한 경우)
    if (currentPage < 2) { // 0, 1 페이지일 때
        endPage = Math.min(4, totalPages - 1);
    }
    if (currentPage > totalPages - 3) { // 마지막 2페이지일 때
        startPage = Math.max(0, totalPages - 5);
    }
    
    // (시작 페이지가 0보다 클 경우) 첫 페이지로 가기
    if (startPage > 0) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="loadSales(0); return false;">1</a></li>`;
        if (startPage > 1) {
             html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }

    // 페이지 번호 (startPage ~ endPage)
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="loadSales(${i}); return false;">
                    ${i + 1}
                </a>
            </li>
        `;
    }

    // (끝 페이지가 totalPages보다 작을 경우) 마지막 페이지로 가기
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
    
    html += '</ul>';
    pagination.innerHTML = html;
}

/**
 * 숫자 포맷 (콤마)
 */
function formatNumber(num) {
    return new Intl.NumberFormat('ko-KR').format(num || 0);
}

/**
 * 필터 적용
 */
function applyFilters() {
    // 💡 [수정] 모바일/PC 검색창 값 동기화
    syncSearchInputs();
    // 필터 적용 시 항상 0페이지(첫 페이지)부터 검색
    loadSales(0);
    
    // 💡 [추가] 모바일에서 "필터 적용" 클릭 시 Offcanvas 닫기
    const offcanvasElement = document.getElementById('filterOffcanvas');
    if (offcanvasElement) {
        const offcanvas = bootstrap.Offcanvas.getInstance(offcanvasElement);
        if (offcanvas) {
            offcanvas.hide();
        }
    }
}

/**
 * 💡 [추가] 페이지 로드 시 URL 파라미터로 필터/페이지 복원
 */
function loadSalesFromUrl() {
    const params = new URLSearchParams(window.location.search);
    
    const page = parseInt(params.get('page') || '0', 10);
    const keyword = params.get('keyword') || '';
    
    // 💡 [수정] 모바일/PC 검색창 모두 복원
    document.getElementById('searchInputPc').value = keyword;
    document.getElementById('searchInputMobile').value = keyword;
    
    if (document.getElementById('sortBy')) {
        document.getElementById('sortBy').value = params.get('sortBy') || 'latest';
    }
    if (document.getElementById('minPrice')) {
        document.getElementById('minPrice').value = params.get('minPrice') || 0;
    }
    if (document.getElementById('maxPrice')) {
        document.getElementById('maxPrice').value = params.get('maxPrice') || 10000000;
    }
    
    const sources = params.getAll('sources');
    if (sources.length > 0) {
        document.querySelectorAll('input[type="checkbox"][id^="site-"]').forEach(cb => {
            cb.checked = sources.includes(cb.value);
        });
    }
    
    loadSales(page);
}

// 💡 [추가] 두 검색창 값을 동기화하는 함수
function syncSearchInputs() {
     const keywordPc = document.getElementById('searchInputPc');
     const keywordMobile = document.getElementById('searchInputMobile');
     if (!keywordPc || !keywordMobile) return; // 페이지에 요소가 없는 경우 종료
     
     // PC 검색창이 보이는 상태이면, 모바일 검색창 값을 PC로 복사
     if (window.getComputedStyle(keywordPc).display !== 'none') {
         if(keywordMobile.value) keywordPc.value = keywordMobile.value;
     } 
     // 모바일 검색창이 보이는 상태이면, PC 검색창 값을 모바일로 복사
     else if (window.getComputedStyle(keywordMobile).display !== 'none') {
         if(keywordPc.value) keywordMobile.value = keywordPc.value;
     }
}

// ---------------------------------------------
// [main.js]의 함수들 (중복 방지)
// ---------------------------------------------

/**
 * 날짜 포매팅
 */
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60); // 💡 1000 -> 60 수정
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 7) {
        return date.toLocaleDateString('ko-KR');
    } else if (days > 0) {
        return `${days}일 전`;
    } else if (hours > 0) {
        return `${hours}시간 전`;
    } else if (minutes > 0) {
         return `${minutes}분 전`;
    } else {
        return '방금 전';
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