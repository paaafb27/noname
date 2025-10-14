package com.project.scandeals.domain.user.repository;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.project.scandeals.common.entity.AuthProvider;
import com.project.scandeals.domain.user.entity.User;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {

	/**
	 * 이메일로 사용자 조회
	 */
	Optional<User> findByEmail(String email);
	
	/**
     * OAuth 제공자와 제공자 ID로 사용자 조회
     */
	Optional<User> findByProviderAndProviderId(AuthProvider provider, String providerId);
	
	/**
	 * 이메일 중복 확인
	 */
	boolean existsByEmail(String email);
	
	/**
     * OAuth 제공자와 제공자 ID 존재 여부
     */
    boolean existsByProviderAndProviderId(AuthProvider provider, String providerId);
    
}
