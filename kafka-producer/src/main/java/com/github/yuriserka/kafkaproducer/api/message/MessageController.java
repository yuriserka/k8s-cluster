package com.github.yuriserka.kafkaproducer.api.message;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

import com.github.yuriserka.kafkaproducer.api.message.usecase.SendMessageToUserUseCase;

import lombok.RequiredArgsConstructor;

@RestController
@RequiredArgsConstructor
public class MessageController {
    private final SendMessageToUserUseCase sendMessageToUserUseCase;

    @GetMapping("/produce/{username}")
    public ResponseEntity<Void> produceMessage(@PathVariable("username") final String username) {
        sendMessageToUserUseCase.execute(username);
        return ResponseEntity.ok().build();
    }
}
