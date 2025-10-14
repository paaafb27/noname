package com.project.scandeals.security.jwt;

import java.io.IOException;
import java.util.ArrayList;

import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

/**
 * JWT 인증 필터
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {
	
	private final JwtTokenProvider jwtTokenProvider;
	
	@Override
	protected void doFilterInternal(
			HttpServletRequest request,
			HttpServletResponse response,
			FilterChain filterChain) throws ServletException, IOException {
	
		// Authorization 헤더에서 토큰 추출
		String token = resolveToken(request);
		
		if (token != null && jwtTokenProvider.validateToken(token)) {
			
			Long userId = jwtTokenProvider.getUserId(token);
			// SecurityContext에 인증 정보 저장
			UsernamePasswordAuthenticationToken authentication =
					new UsernamePasswordAuthenticationToken(userId, null, new ArrayList<>());
			
			SecurityContextHolder.getContext().setAuthentication(authentication);
			
			log.debug("JWT 인증 성공 : userId={}", userId);
		}
		
		filterChain.doFilter(request, response);
	}
	
	/**
     * Authorization 헤더에서 Bearer 토큰 추출
     */
	private String resolveToken(HttpServletRequest request) {
		
		String bearerToken = request.getHeader("Authorization");
		
		if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
			return bearerToken.substring(7);
		}
		
		return null;
	}
	
	

}
