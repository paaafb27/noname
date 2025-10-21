package com.project.scandeals.security.oauth;

import java.util.Map;

import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.project.scandeals.common.entity.AuthProvider;
import com.project.scandeals.domain.user.entity.User;
import com.project.scandeals.domain.user.repository.UserRepository;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

/**
 * OAuth 2.0 사용자 정보 처리
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CustomOAuth2UserService extends DefaultOAuth2UserService {

    private final UserRepository userRepository;
    
    @Override
    @Transactional
    public OAuth2User loadUser(OAuth2UserRequest userRequest) 
            throws OAuth2AuthenticationException {
    	
    	// ======================= 디버깅 로그 추가 =======================
        log.info("======================================================");
        log.info("getClientRegistration: {}", userRequest.getClientRegistration());
        log.info("getAccessToken: {}", userRequest.getAccessToken().getTokenValue());
        // =============================================================
        
        // 1. OAuth 2.0 사용자 정보 로드
        OAuth2User oAuth2User = super.loadUser(userRequest);
        
     // ======================= 디버깅 로그 추가 =======================
        log.info("oAuth2User.getAttributes: {}", oAuth2User.getAttributes());
        log.info("======================================================");
        // =============================================================
        
        // 2. OAuth 제공자 확인
        String registrationId = userRequest.getClientRegistration()
            .getRegistrationId();
        AuthProvider provider = AuthProvider.valueOf(registrationId.toUpperCase());
        
        // 3. 사용자 정보 추출
        Map<String, Object> attributes = oAuth2User.getAttributes();
        
        // ⭐ 디버깅: 받은 속성 전체 출력
        log.info("=== OAuth 속성 전체 ===");
        attributes.forEach((key, value) -> 
            log.info("  {} = {}", key, value)
        );
        
        // 4. sub 속성 확인
        Object subObj = attributes.get("sub");
        if (subObj == null) {
            log.error("❌ 'sub' 속성이 null입니다!");
            log.error("받은 속성: {}", attributes);
            throw new OAuth2AuthenticationException("Google 사용자 정보에 'sub' 속성이 없습니다.");
        }
        
        String providerId = subObj.toString();
        String email = attributes.get("email").toString();
        String name = attributes.get("name").toString();
        
        log.info("✅ OAuth 사용자 정보: providerId={}, email={}, name={}", 
            providerId, email, name);
        
        // 5. DB에서 사용자 조회 또는 생성
        User user = userRepository.findByProviderAndProviderId(provider, providerId)
            .map(existingUser -> {
                existingUser.updateInfo(name);
                return userRepository.save(existingUser);
            })
            .orElseGet(() -> {
                User newUser = User.builder()
                    .email(email)
                    .name(name)
                    .nickname(generateNickname(name))
                    .provider(provider)
                    .providerId(providerId)
                    .build();
                return userRepository.save(newUser);
            });
        
        log.info("✅ OAuth 로그인 성공: userId={}, email={}", user.getId(), user.getEmail());
        
        return new CustomOAuth2User(user, attributes);
    }
    
    /**
     * 닉네임 자동 생성
     */
    private String generateNickname(String name) {
        return name + "_" + System.currentTimeMillis() % 10000;
    }
}