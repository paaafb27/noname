/**
 * 공통 함수
 */

/**
 * 가격 포매팅
 */
function formatPrice(price) {
    if (!price) return '가격 문의';
    return new Intl.NumberFormat('ko-KR').format(price);
}

/**
 * 숫자 포매팅
 */
function formatNumber(num) {
    if (!num) return '0';
    return new Intl.NumberFormat('ko-KR').format(num);
}

/**
 * 날짜 포매팅
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 1000);
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
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * 로그인 상태 확인
 */
function isLoggedIn() {
    return !!localStorage.getItem('accessToken');
}

/**
 * 인증이 필요한 요청
 */
async function fetchWithAuth(url, options = {}) {
    const accessToken = localStorage.getItem('accessToken');
    
    if (!accessToken) {
        throw new Error('로그인이 필요합니다');
    }
    
    options.headers = {
        ...options.headers,
        'Authorization' : `Bearer ${accessToken}`
    };
    
    let response = await fetch(url, options);
    
    // 401 에러 발생 시 토큰 갱신 시도
    if (response.status === 401) {
        const refreshed = await refreshaccessToken();
        
        if (refreshed) {
            options.headers['Authorization'] = `Bearer ${localStorage.getItem('accessToken')}`;
        } else {
            // 갱신 실패
            alert('로그인이 만료되었습니다. 다시 로그인해주세요.');
            location.href = '/login';
        }
        
        return response;
    }
}

/**
 * Access Token 갱신
 */
async function refreshAccessToken() {
    const refreshToken = localStorage.getItem('accessToken');
    
    if (!refreshToken) {
        return false;
    }
    
    try {
        const response = await fetch('/api/auth/refresh', {
            method : 'POST',
            headers : {'Content-Type' : 'application/json'},
            body : JSON.stringify({refreshToken})
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('accessToken', data.accessToken);
            return true;
        }
    } catch (error) {
        console.error('토큰 갱신 실패 : ', error);
    }
    
    return false;
}

/**
 * 로그아웃
 */
function logout() {
    if (confirm('로그아웃 하시겠습니까?')) {
        location.href = '/logout';
    }
}

/**
 * OAuth 리다이렉트
 */
if (window.location.pathname === '/oauth/redirect') {
    const params = new URLSearchParams(window.location.search);
    const accessToken = params.get('accessToken');
    const refreshToken = params.get('refreshToken');
    
    if (accessToken && refreshToken) {
        localStorage.setItem('accessToken', accessToken);
        localStorage.setItem('refreshToken', refreshToken);
        location.href = '/';
    }
    
}