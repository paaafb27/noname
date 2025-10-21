package com.project.scandeals.web.controller;

import org.springframework.security.web.bind.annotation.AuthenticationPrincipal;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import com.project.scandeals.security.oauth.CustomOAuth2User;

@Controller
public class HomeController {

	/*
	 * 메인
	 */
	@GetMapping("/")
	public String home(@AuthenticationPrincipal CustomOAuth2User oAuth2User, Model model) {
		
		if (oAuth2User != null) {
			model.addAttribute("userName", oAuth2User.getUser().getName());
			model.addAttribute("userEmail", oAuth2User.getUser().getEmail());
		}
		
		return "index";
	}
	
	/*
	 * 로그인
	 */
	@GetMapping("/login")
    public String login() {
        return "auth/login";
    }
}
