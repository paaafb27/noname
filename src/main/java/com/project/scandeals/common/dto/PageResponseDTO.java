package com.project.scandeals.common.dto;

import java.util.List;

import org.springframework.data.domain.Page;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/** 
 * 페이징 응답 DTO
 * 
 * @Param <T> 응답 데이터 타입
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PageResponseDTO<T> {

	private List<T> content;			/** 데이터 목록 */
	private int page;					/** 현재 페이지 번호 (0부터) */
	private int size;					/** 페이지당 데이터 수 */
	private long totalElements;			/** 전체 데이터 수 */
	private int totalPages;				/** 전체 페이지 수 */
	private boolean isFirst;			/** 첫 페이지 여부 */
	private boolean isLast;				/** 마지막 페이지 여부 */
	private boolean isEmpty;			/** 빈 페이지 여부 */
	
	/**
	 * Spring Data Page -> PageResponse 변환
	 */
	public static <T> PageResponseDTO<T> from(Page<T> page) {
		
		return PageResponseDTO.<T>builder()
				.content(page.getContent())
				.page(page.getNumber())
				.size(page.getSize())
				.totalElements(page.getTotalElements())
				.totalPages(page.getTotalPages())
				.isFirst(page.isFirst())
				.isLast(page.isLast())
				.isEmpty(page.isEmpty())
				.build();
	}
	
	/**
     * List와 페이징 정보로 생성 (Redis 캐시용)
     * 
     * Redis에서 가져온 List를 PageResponseDTO로 변환
     * 캐시된 데이터를 페이징 형태로 반환
     */
    public static <T> PageResponseDTO<T> of(List<T> content, int page, int size, long totalElements) {
			
    	int totalPages = (int) Math.ceil((double) totalElements / size);
    	
    	return PageResponseDTO.<T>builder()
                .content(content)
                .page(page)
                .size(size)
                .totalElements(totalElements)
                .totalPages(totalPages)
                .isFirst(page == 0)
                .isLast(page >= totalPages - 1)
                .isEmpty(content.isEmpty())
                .build();
    }
}
