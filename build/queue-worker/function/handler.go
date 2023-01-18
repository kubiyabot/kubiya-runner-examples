package function

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	nats "github.com/nats-io/nats.go"
	handler "github.com/openfaas/templates-sdk/go-http"
)

type MessageBody struct {
	InboxId string      `json:"inbox_id"`
	Output  interface{} `json:"output"`
	Runner  string      `json:"runner"`
}

// Handle a function invocation
func Handle(req handler.Request) (handler.Response, error) {
	// print the request body as a string
	fmt.Println("Received body: " + string(req.Body))
	msg := "default message"
	if len(req.Body) > 0 {
		msg = string(bytes.TrimSpace(req.Body))
	}
	nc, err := nats.Connect("tls://connect.ngs.global", nats.UserCredentials("/var/openfaas/secrets/nts-tkn"))
	if err != nil {
		errMsg := fmt.Sprintf("can not connect to nats: %s", err)
		log.Printf(errMsg)
		r := handler.Response{
			Body:       []byte(errMsg),
			StatusCode: http.StatusInternalServerError,
		}
		return r, err
	}
	defer nc.Close()
	var messageBody MessageBody
	log.Printf("request body: %s", req.Body)
	jsonErr := json.Unmarshal(req.Body, &messageBody)
	if jsonErr != nil {
		log.Printf("Error unmarshalling request body: %s", jsonErr)
		r := handler.Response{
			Body:       []byte("Error unmarshalling request body"),
			StatusCode: http.StatusInternalServerError,
		}
		return r, err
	}
	inboxId := messageBody.InboxId
	runner := messageBody.Runner
	log.Printf("Publishing %d bytes to: %q\n", len(msg), messageBody.InboxId)

	err = nc.PublishRequest(runner+".response", inboxId, []byte(msg))
	if err != nil {
		log.Printf("Error publishing to nats: %s", err)
		r := handler.Response{
			Body:       []byte(fmt.Sprintf("can not publish to NATS: %s", err)),
			StatusCode: http.StatusInternalServerError,
		}
		return r, err
	}

	return handler.Response{
		Body:       []byte(fmt.Sprintf("Published %d bytes to: %q", len(msg), "runner")),
		StatusCode: http.StatusOK,
	}, nil
}
