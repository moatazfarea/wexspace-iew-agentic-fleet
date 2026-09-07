# Cross-Opportunity Reuse Map

Goal: every hour spent on Agents for Humans should also strengthen WEXSPACE and reduce work for later opportunities.

| Capability built here | WEXSPACE Core value | Agents for Humans | Amazon Build/Ship/Shape | OpenCV 2026 | Nebius/NVIDIA |
|---|---|---|---|---|---|
| Event cursor / resume | SPINE-002 durable state | High | High | High | High |
| Work-intake schema | Command/compiler precursor | High | High | Medium | High |
| Missing-input control | Governance / human boundary | High | High | High | High |
| Evidence/provenance package | Evidence plane | High | High | High | High |
| Human decision gate | Human release plane | High | High | High | High |
| Provider adapter boundary | Provider/model broker | Medium | High | Medium | High |
| Tool registry interface | Capability fabric | High | High | High | High |
| Evaluation harness | Universal evaluation | High | High | High | High |
| Observability/event trace | Observability plane | High | High | High | High |
| MCP-compatible façade | External capability interface | Optional | **Very High for Alexa+** | Medium | Medium |
| Vision-result action hook | Multimodal action loop | Low now | Medium | **Very High** | Medium |

## Recommended architecture split

`core/`
- typed work request
- task/event state
- event cursor
- evidence/provenance
- human decision contract
- evaluation hooks

`providers/strands/`
- Strands agent adapter
- Bedrock/AgentCore integration when available

`interfaces/mcp/`
- future MCP façade for Amazon Alexa+ path

`adapters/vision/`
- future OpenCV perception-to-action adapter

`providers/nebius/`
- future Nemotron/Nebius model adapter

This preserves one tested professional-execution kernel while keeping competition-specific implementation isolated and truthful.
