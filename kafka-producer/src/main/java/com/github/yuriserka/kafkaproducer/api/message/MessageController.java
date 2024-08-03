package com.github.yuriserka.kafkaproducer.api.message;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.github.yuriserka.kafkaproducer.api.message.usecases.SendMessageToUserUseCase;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@RestController
@RequiredArgsConstructor
@RequestMapping("/message")
@Slf4j
public class MessageController {
    private final SendMessageToUserUseCase sendMessageToUserUseCase;

    @GetMapping("/{username}")
    public ResponseEntity<Void> produceMessage(@PathVariable final String username) {
        log.info("Sending message to user {}", username);
        sendMessageToUserUseCase.execute(username);
        return ResponseEntity.ok().build();
    }
}
