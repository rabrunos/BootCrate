# Discovery coverage for the future intake

This is reusable question-design guidance, not an active roadmap or a second copy of user answers. The current questionnaire remains unchanged. Until its redesign, ChatGPT asks these in conversation when the answers affect design.

| Owner-language topic | Technical conclusion to derive |
| --- | --- |
| Who can use this, locally or over the internet? | Exposure, authentication, authorization and peer boundaries |
| Will people upload files or send messages/content? | Parser, XSS, upload, quota and abuse controls |
| Will it store private identity, documents or payment information? | Data minimization, sensitive-data module, review and operation requirements |
| Does it open files, run tools or receive player commands? | Filesystem/process/IPC/native threat boundaries |
| What must be online or synchronized? | Minimal external capabilities, not a predefined provider list |
| Spend less money, do less maintenance, or retain more control? | Managed/self-hosted/hybrid comparison with total operating cost |
| Who maintains services and restores backups? | Operational ownership; unresolved ownership blocks deployment |
| What scale, downtime, data loss and monthly ceiling are acceptable? | Capacity, recovery, monitoring and cost controls |
| What services or infrastructure already exist? | Reuse when suitable; no automatic account/server changes |

Do not turn mandatory safety controls into optional questions such as 'Do you want injection protection?'. Unknown is valid owner input; unresolved material risk is not permission to deploy.
