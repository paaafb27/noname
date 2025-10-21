package com.project.scandeals.web.controller;

import org.springframework.security.core.annotation.AuthenticationPrincipal;  // 올바른 import
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import com.project.scandeals.security.oauth.CustomOAuth2User;

/**
 * 홈 컨트롤러
 */
@Controller
public class HomeController {

    /**
     * 메인 페이지
     */
    @GetMapping("/")
    public String home(@AuthenticationPrincipal CustomOAuth2User oAuth2User, Model model) {
        
        if (oAuth2User != null) {
            model.addAttribute("userName", oAuth2User.getUser().getName());
            model.addAttribute("userEmail", oAuth2User.getUser().getEmail());
            model.addAttribute("isLoggedIn", true);
        } else {
            model.addAttribute("isLoggedIn", false);
        }
        
        return "index";
    }
    
    /**
     * 로그인 페이지
     */
    @GetMapping("/login")
    public String login() {
        return "auth/login";
    }
}