//package com.project.scandeals.security.oauth;
//
//import java.util.Collection;
//import java.util.Collections;
//import java.util.Map;
//
//import org.springframework.security.core.GrantedAuthority;
//import org.springframework.security.oauth2.core.user.OAuth2User;
//
//import com.project.scandeals.domain.user.entity.User;
//
//import lombok.Getter;
//
///**
// * OAuth 2.0 인증된 사용자 정보
// */
//@Getter
//public class CustomOAuth2User implements OAuth2User {
//
//	private final User user;
//	private final Map<String, Object> attributes;
//	
//	public CustomOAuth2User(User user, Map<String, Object> attributes) {
//		this.user = user;
//		this.attributes = attributes;
//	}
//	
//	@Override
//	public Map<String, Object> getAttributes() {
//		return attributes;
//	}
//	
//	@Override
//	public Collection<? extends GrantedAuthority> getAuthorities() {
//		return Collections.emptyList();
//	}
//	
//	@Override
//	public String getName() {
//		return user.getId().toString();
//	}
//	
//	
//}
