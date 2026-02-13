package protocol

import (
	"encoding/json"

	"github.com/vmihailenco/msgpack/v5"
)

// Codec handles message encoding and decoding
type Codec struct{}

// NewCodec creates a new codec
func NewCodec() *Codec {
	return &Codec{}
}

// EncodeMsgpack encodes a message to MessagePack bytes
func (c *Codec) EncodeMsgpack(msg *Message) ([]byte, error) {
	return msgpack.Marshal(msg)
}

// DecodeMsgpack decodes MessagePack bytes to a message
func (c *Codec) DecodeMsgpack(data []byte) (*Message, error) {
	var msg Message
	if err := msgpack.Unmarshal(data, &msg); err != nil {
		return nil, err
	}
	return &msg, nil
}

// EncodeJSON encodes a message to JSON bytes (fallback)
func (c *Codec) EncodeJSON(msg *Message) ([]byte, error) {
	return json.Marshal(msg)
}

// DecodeJSON decodes JSON bytes to a message (fallback)
func (c *Codec) DecodeJSON(data []byte) (*Message, error) {
	var msg Message
	if err := json.Unmarshal(data, &msg); err != nil {
		return nil, err
	}
	return &msg, nil
}

// Decode tries MessagePack first, then falls back to JSON
func (c *Codec) Decode(data []byte) (*Message, error) {
	msg, err := c.DecodeMsgpack(data)
	if err != nil {
		// Fallback to JSON
		return c.DecodeJSON(data)
	}
	return msg, nil
}

// Encode encodes to MessagePack by default
func (c *Codec) Encode(msg *Message) ([]byte, error) {
	return c.EncodeMsgpack(msg)
}
