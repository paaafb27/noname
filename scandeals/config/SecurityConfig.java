package com.project.scandeals.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

import com.project.scandeals.security.jwt.JwtAuthenticationFilter;
import com.project.scandeals.security.oauth.CustomOAuth2UserService;
import com.project.scandeals.security.oauth.OAuth2SuccessHandler;

import lombok.RequiredArgsConstructor;

/**
 * Spring Security
 * 
 * 1. OAuth 2.0 소셜로그인
 * 2. JWT 토큰 기반 인증
 */

@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

	private final CustomOAuth2UserService customOAuth2UserService;
	private final OAuth2SuccessHandler oAuth2SuccessHandler;
	private final JwtAuthenticationFilter jwtAuthenticationFilter;
	
	@Bean
	public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
		
		http
			.csrf(csrf -> csrf.disable())										// CSRF 비활성화 (JWT 사용으로 불필요)
//			.cors(cors -> cors.configurationSource(corsConfigurationSource()))	// CORS 설정
			.sessionManagement(session -> 
				session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))	// 세션 사용 안 함(JWT로 stateless 인증)
			.authorizeHttpRequests(auth -> auth									// URL별 권한 설정
					// 공개 API
					.requestMatchers(
							"/",
		                    "/api/sales/**",      								// 세일 조회
		                    "/api/health/**",      								
		                    "/login",            								// 로그인 관련
		                    "/oauth/**",        								// OAuth 콜백
		                    "/swagger-ui/**",          							// Swagger UI
		                    "/v3/api-docs/**"          							// API 문서
							).permitAll()
					// 인증 필요 API
					.requestMatchers(
							"/api/comments/**",        							// 댓글 작성/수정/삭제
		                    "/api/likes/**"           							// 좋아요
							).authenticated()
					// 관리자 전용
					.requestMatchers("/api/admin/**").hasRole("ADMIN")
					// 그 외
					.anyRequest().authenticated()
			)
			// OAuth 2.0 설정
			.oauth2Login(oauth -> oauth
					.userInfoEndpoint(userInfo ->
							userInfo.userService(customOAuth2UserService))
					.successHandler(oAuth2SuccessHandler)
			)
			// JWT 필터 추가 (UsernamePasswordAuthenticationFilter 전에 실행)
			.addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);
		
		return http.build();
	}
	
//	/**
//	 * CORS 설정
//	 * 프론트엔드에서 API 호출 허용
//	 */
//	@Bean
//	public CorsConfigurationSource corsConfigurationSource() {
//		
//		CorsConfiguration config = new CorsConfiguration();
//		
//		config.setAllowedOrigins(Arrays.asList(
//				"http://localhost:3000",      // React 개발 서버
//	            "http://localhost:8080",      // 같은 도메인
//	            "https://scandelas.net"       // 운영 도메인
//				));
//		
//		config.setAllowedMethods(Arrays.asList(
//				"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"
//		));
//		
//		config.setAllowedHeaders(Arrays.asList("*"));
//		config.setAllowCredentials(true);
//		config.setMaxAge(3600L);
//		
//		UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
//		source.registerCorsConfiguration("/**", config);
//		
//		return source;
//	}
}
