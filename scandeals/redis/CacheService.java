/*
package com.project.scandeals.redis;

import static org.springframework.test.web.servlet.result.MockMvcResultHandlers.log;

import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class CacheService {
	
	private final RedisTemplate<String, String> redisTemplate;

	@Transactional
    public void onCommentCreate(Long saleId) {
        // Tier 2: 상세만 무효화
        redisTemplate.delete("sale:id:" + saleId);
        
        log.info("캐시 무효화: sale:id:{} (댓글 작성)", saleId);
    }
    
    @Transactional
    public void onPriceChange(Long saleId) {
        // Tier 1: 모든 캐시 무효화
        redisTemplate.delete("sale:id:" + saleId);
        redisTemplate.delete("sale:list:*");
        
        log.info("전체 캐시 무효화: sale:id:{} (가격 변경)", saleId);
    }
    
    @Scheduled(fixedRate = 300000) // 5분마다
    public void syncViewCount() {
        // Tier 3: 주기적 동기화
        // Redis 카운터 → MySQL 배치 업데이트
    }
}
*/