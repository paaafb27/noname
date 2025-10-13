package com.project.scandeals.domain.saleLike.repository;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.project.scandeals.domain.saleLike.entity.SaleLike;

@Repository
public interface SaleLikeRepository extends JpaRepository<SaleLike, Long> {

	/**
     * 좋아요 존재 여부
     */
    boolean existsBySaleIdAndUserId(Long saleId, Long userId);
    
    /**
     * 좋아요 조회
     */
    Optional<SaleLike> findBySaleIdAndUserId(Long saleId, Long userId);
    
    /**
     * 세일별 좋아요 개수
     */
    long countBySaleId(Long saleId);
}
