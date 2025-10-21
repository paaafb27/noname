package com.project.scandeals.security.oauth;

import java.io.IOException;

import org.springframework.security.core.Authentication;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationSuccessHandler;
import org.springframework.stereotype.Component;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
import lombok.extern.slf4j.Slf4j;

/**
 * OAuth 로그인 성공 시 JWT 발급
 * 
 * Access Token(30분) + Refresh Token(14일) 생성
 * 자동 로그인 유지, 보안 강화
 */
@Slf4j
@Component
public class OAuth2SuccessHandler extends SimpleUrlAuthenticationSuccessHandler {

    @Override
    public void onAuthenticationSuccess(
            HttpServletRequest request,
            HttpServletResponse response,
            Authentication authentication
    ) throws IOException {
        
        CustomOAuth2User oAuth2User = (CustomOAuth2User) authentication.getPrincipal();
        
        // 세션에 사용자 정보 저장 (Spring Security가 자동으로 처리)
        HttpSession session = request.getSession();
        session.setAttribute("userId", oAuth2User.getUser().getId());
        session.setAttribute("userName", oAuth2User.getUser().getName());
        session.setAttribute("userEmail", oAuth2User.getUser().getEmail());
        
        log.info("세션 로그인 성공: userId={}, sessionId={}", 
            oAuth2User.getUser().getId(), session.getId());
        
        // 메인 페이지로 리다이렉트
        getRedirectStrategy().sendRedirect(request, response, "/");
    }
}
