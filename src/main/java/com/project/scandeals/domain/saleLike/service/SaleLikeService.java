package com.project.scandeals.domain.saleLike.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.project.scandeals.domain.sale.entity.Sale;
import com.project.scandeals.domain.sale.repository.SaleRepository;
import com.project.scandeals.domain.saleLike.entity.SaleLike;
import com.project.scandeals.domain.saleLike.repository.SaleLikeRepository;
import com.project.scandeals.domain.user.entity.User;
import com.project.scandeals.domain.user.repository.UserRepository;
import com.project.scandeals.redis.RedisService;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class SaleLikeService {
	
	private final SaleLikeRepository saleLikeRepository;
    private final SaleRepository saleRepository;
    private final UserRepository userRepository;
    private final RedisService redisService;
    
    /**
     * 좋아요 토글
     */
    @Transactional
    public boolean toggleLike(Long saleId, Long userId) {
    	
    	Sale sale = saleRepository.findById(saleId)
                .orElseThrow(() -> new IllegalArgumentException("세일을 찾을 수 없습니다."));
    	
    	User user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다."));
    	
    	// 좋아요한 경우 > 취소
    	if (saleLikeRepository.existsBySaleIdAndUserId(saleId, userId)) {
    		SaleLike like = saleLikeRepository.findBySaleIdAndUserId(saleId, userId)
    				.orElseThrow();
    		
    		saleLikeRepository.delete(like);
    		sale.updateLikeCount(-1);
    		
    		// Redis 캐시 무효화
        	redisService.deleteCache("sale:id:" + saleId);
        	
        	log.info("좋아요 취소 : saleId={}, userId={}", saleId, userId);
            return false;
    	}
    	
    	// 좋아요 추가
    	SaleLike like = SaleLike.builder()
    			.sale(sale)
    			.user(user)
    			.build();
    	
    	saleLikeRepository.save(like);
    	sale.updateLikeCount(1);
    	
    	// Redis 캐시 무효화
    	redisService.deleteCache("sale:id:" + saleId);
    	
    	log.info("좋아요 추가 : saleId={}, userId={}", saleId, userId);
        return true;
    }
    
    /**
     * 좋아요 여부 확인
     */
    public boolean isLiked(Long saleId, Long userId) {
    	
    	return saleLikeRepository.existsBySaleIdAndUserId(saleId, userId); 
   }

}
