//package com.project.scandeals.security.oauth;
//
//import java.io.IOException;
//import java.util.concurrent.TimeUnit;
//
//import org.springframework.beans.factory.annotation.Value;
//import org.springframework.data.redis.core.RedisTemplate;
//import org.springframework.security.core.Authentication;
//import org.springframework.security.web.authentication.SimpleUrlAuthenticationSuccessHandler;
//import org.springframework.stereotype.Component;
//import org.springframework.web.util.UriComponentsBuilder;
//
//import com.project.scandeals.domain.user.entity.User;
//import com.project.scandeals.security.jwt.JwtTokenProvider;
//
//import jakarta.servlet.http.HttpServletRequest;
//import jakarta.servlet.http.HttpServletResponse;
//import lombok.RequiredArgsConstructor;
//import lombok.extern.slf4j.Slf4j;
//
///**
// * OAuth 로그인 성공 시 JWT 발급
// * 
// * Access Token(30분) + Refresh Token(14일) 생성
// * 자동 로그인 유지, 보안 강화
// */
//@Slf4j
//@Component
//@RequiredArgsConstructor
//public class OAuth2SuccessHandler extends SimpleUrlAuthenticationSuccessHandler {
//
//	private final JwtTokenProvider jwtTokenProvider;
//	private final RedisTemplate<String, String> redisTemplate;
//	
//	@Value("${app.oauth2.redirect-uri:http://localhost:8080/oatuh/redirect}")
//	private String redirectUri;
//	
//	@Override
//	public void onAuthenticationSuccess(
//			HttpServletRequest request,
//			HttpServletResponse response,
//			Authentication authentication
//	) throws IOException {
//		
//		CustomOAuth2User oAuth2User = (CustomOAuth2User) authentication.getPrincipal();
//		User user = oAuth2User.getUser();
//		
//		// JWT 토큰 생성
//		String accessToken = jwtTokenProvider.createAccessToken(user.getId(), user.getEmail());
//		String refreshToken = jwtTokenProvider.createRefreshToken(user.getId());
//		
//		// Refresh Token을 Redis에 저장 (14일)
//		String refreshKey = "refresh_token : " + user.getId();
//		redisTemplate.opsForValue().set(refreshKey, refreshToken, 14, TimeUnit.DAYS);
//		
//		log.info("JWT 토큰 발급 완료 : userId={}", user.getId());
//		
//		// 프런트로 리다이렉트(토큰 전달)
//		String targetUrl = UriComponentsBuilder.fromUriString(redirectUri)
//				.queryParam("accessToken", accessToken)
//				.queryParam("refreshToken", refreshToken)
//				.build()
//				.toUriString();
//		
//		getRedirectStrategy().sendRedirect(request, response, targetUrl);
//	}
//	
//}
