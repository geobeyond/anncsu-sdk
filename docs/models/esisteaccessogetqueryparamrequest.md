# EsisteAccessoGetQueryParamRequest


## Fields

| Field                                                              | Type                                                               | Required                                                           | Description                                                        | Example                                                            |
| ------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `codcom`                                                           | *str*                                                              | :heavy_check_mark:                                                 | Codice Belfiore del comune dell'odonimo                            | H501                                                               |
| `denom`                                                            | *str*                                                              | :heavy_check_mark:                                                 | Denominazione esatta dell'odonimo - base64 encoded                 | VklBIFJPTUE=                                                       |
| `accesso`                                                          | *str*                                                              | :heavy_check_mark:                                                 | valore civico(+eventuale esponente e/o specificit�) oppure metrico | 42                                                                 |