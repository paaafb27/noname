/**
 * 세일 목록
 */
let currentPage = 0;
const pageSize = 12;

async function loadSaleList(page = 0) {
    const loading = document.getElementById('loading');
    const saleList = document.getElementById('saleList');
    
    // 로딩 표시
    loading.style.display = 'block';
    saleList.style.display = 'none';
    
    try {
        // 필터 조건
        const sourceSites = Array.from(document.querySelectorAll('.filter-section input[type="checkbox"]:checked'))
            .filter(cb => cb.value)
            .map(cb => cb.value )
            
        const categories = Array.from(document.querySelectorAll('.filter-section input[id^="cat-"]::checked'))
            .filter(cb => cb.value)
            .map(cb => cb.value);
            
        const minPrice = document.getElementById('minPrice').value || 0;
        const maxPrice = document.getElementById('maxPrice').value || 10000000;
        
        // API 호출
        const params = new URLSearchParams({
            page: page,
            size: pageSize,
            sortBy: sortBy,
            minPrice: minPrice,
            maxPrice: maxPrice
        });
        
        sourceSites.forEach(s => params.append('sources', s));
        categories.forEach(c => params.append('categories', c));
        
        const response = await fetch('/api/sales?${params.toString()}');
        const data = await response.json();
        
        // 목록
        loadSaleList(data.content);
        loadPagination(data);
        
        // 총 개수 업데이트
        document.getElementById('totalCount').textContent = data.totalElements;
        
        currentPage = page;
            
    } catch (error) {
        console.log('세일 목록 로드 실패 : ', error);
        saleList.innerHTML = '<div class="col-12 text-center py-5"><p class="text-danger">데이터를 불러올 수 없습니다.</p></div>';
        
    } finally {
        loading.style.display = 'none';
        saleList.style.display = 'flex';
    }
}

/**
 * 세일 카드 렌더링
 */
function loadSaleList(sales) {
    const saleList = document.getElementById('saleList');
    
    if (sales.length === 0) {
        saleList.innerHTML = '<div class="col-12 text-center py-5"><p class="text-muted">검색 결과가 없습니다.</p></div>';
        return;
    }
    
    saleList.innerHTML = sales.map(sale => `
        <div class="col-lg-4 col-md-6">
            <div class="sale-card position-relative">
                <span class="sale-source-badge">${sale.sourceSite}</span>
                    <a href="/sales/${sale.id}">
                        <img src="${sale.imageUrl || '/images/no-image.png'}" 
                             class="sale-card-img" alt="${sale.title}" loading="lazy">
                    </a>
                    <div class="sale-card-body">
                        <a href="/sales/${sale.id}" class="text-decoration-none">
                            <h5 class="sale-title">${escapeHtml(sale.title)}</h5>
                        </a>
                        <div class="sale-price">${formatPrice(sale.price)}</div>
                        <div class="sale-store">
                            <i class="bi bi-shop"></i> ${sale.storeName}
                        </div>
                        <div class="sale-meta">
                            <span><i class="bi bi-eye"></i> ${formatNumber(sale.viewCount)}</span>
                            <span><i class="bi bi-heart"></i> ${formatNumber(sale.likeCount)}</span>
                            <span><i class="bi bi-chat"></i> ${formatNumber(sale.commentCount)}</span>
                            <span>${formatDate(sale.createdAt)}</span>
                        </div>
                    </div>
            </div>
        </div>`
    ).join('');
}

/**
 * 페이지네이션
 */
function loadPagination(data) {
    const pagination = document.getElementById('pagination');
    const totalPages = data.totalPages;
    const currentPage = data.number;
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '<ul class="pagination">';
    
    // 이전 버튼
    html += `<li class="page-item ${currentPage === 0 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="loadSaleList(${currentPage - 1}); return false;">이전</a>
            </li>`;
    
    // 페이지 번호
    const startPage = Math.max(0, currentPage - 2);
    const endPage = Math.min(totalPages - 1, startPage + 4);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="loadSaleList(${i}); return false;">${i + 1}</a>
                </li>`;
    }
    
    // 다음 버튼
    html += `<li class="page-item ${currentPage === totalPages - 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="loadSales(${currentPage + 1}); return false;">다음</a>
            </li>`;
        
    html += '</ul>';
    pagination.innerHTML = html;
}

/**
 * 필터 초기화
 */
function resetFilters() {
    document.querySelectorAll('.form-check-input').forEach(cb => {
        if (cb.id === 'cat-all' || cb.id.startsWith('ruliweb') || cb.id.startsWith('ppomppu') 
            || cb.id.startsWith('arcalive') || cb.id.startsWith('eomisae') || cb.id.startsWith('fmkorea')
            || cb.id.startsWith('quasarzone')) { 
            cb.checked = true;
        } else {
            cb.checked = false;
        }
    });
    
    document.getElementById('minPrice').value = 0;
        document.getElementById('maxPrice').value = 10000000;
        document.getElementById('sortBy').value = 'latest';
        
        loadSaleList(0);
}