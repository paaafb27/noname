package com.project.scandeals.domain.sale.repository;


import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import com.project.scandeals.domain.sale.entity.Sale;

@Repository
public interface SaleRepository extends JpaRepository<Sale, Long> {

	/**
     * 최신 세일 목록 조회
     */
    Page<Sale> findAllByOrderByCreatedAtDesc(Pageable pageable);
    
    /**
     * 최신 N개 조회 (Redis 캐싱용)
     */
    @Query("SELECT s FROM Sale s " +
    		"ORDER BY s.createdAt DESC")
    List<Sale> findLatestSaleList(Pageable pageable);
    
    /**
     * 출처 사이트별 세일 조회
     */
    Page<Sale> findBySourceSiteOrderByCreatedAtDesc(String sourceSite, Pageable pageable);
    
    /**
     * 상품 URL로 조회
     */
    Optional<Sale> findByProductUrl(String productUrl);
	
	/**
	 * 카테고리별 조회
	 */
	Page<Sale> findByCategoryIdOrderByCreatedAtDesc(Long categoryId, Pageable pageable);
	
	/**
     * 인기 세일 조회 (좋아요 순)
     * 
     * @param since 기준 시간 (현재 - 24시간)
     * @param pageable 페이징 정보
     */
    @Query("SELECT s FROM Sale s " +
    		"WHERE s.createdAt >= :since " +
    		"ORDER BY s.likeCount DESC, s.createdAt DESC")
    Page<Sale> findPopularSales(@Param("since") LocalDateTime since, Pageable pageable);

    /**
     * 조회수 높은 세일 조회
     *
     * @param since 기준 시간 (현재 - 24시간)
     * @param pageable 페이징 정보
     */
    @Query("SELECT s FROM Sale s " +
    		"WHERE s.createdAt >= :since " +
    		"ORDER BY s.viewCount DESC, s.createdAt DESC")
    Page<Sale> findMostViewedSales(@Param("since") LocalDateTime since, Pageable pageable);

    /**
     * 댓글 많은 세일 조회
     * 
     * @param since 기준 시간 (현재 - 48시간)
     */
    @Query("SELECT s FROM Sale s " +
    		"WHERE s.createdAt >= :since " +
    		"ORDER BY s.commentCount DESC, s.createdAt DESC")
    Page<Sale> findMostCommentedSales(@Param("since") LocalDateTime since, Pageable pageable);
	
	/**
	 * 제목으로 검색
	 * 
	 * @param keyword 검색 키워드 ("%키워드%" 형식)
	 */
    @Query("SELECT s FROM Sale s " +
    	       "WHERE s.title LIKE :keyword " +
    	       "ORDER BY s.createdAt DESC")
    Page<Sale> searchByTitle(@Param("keyword") String keyword, Pageable pageable);
    
    /**
     * 특정 기간 세일 조회
     */
    @Query("SELECT s FROM Sale s " +
    		"WHERE s.createdAt BETWEEN :startDate AND :endDate " +
    		"ORDER BY s.createdAt DESC")
    Page<Sale> findByCreatedAtBetween(
    		@Param("startDate") java.time.LocalDateTime startDate,
    		@Param("endDate") java.time.LocalDateTime endDate,
    		Pageable pageable);

}


