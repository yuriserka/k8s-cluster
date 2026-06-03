package com.github.yuriserka.kafkaproducer.api.message;

import com.github.yuriserka.kafkaproducer.api.message.usecases.SendMessageToUserUseCase;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/message")
public class MessageController {

  private final SendMessageToUserUseCase sendMessageToUserUseCase;

  @GetMapping("/{username}")
  public void produceMessage(@PathVariable final String username) {
    sendMessageToUserUseCase.execute(UUID.randomUUID().toString(), username);
  }
}
