# Quy tắc viết bảng Requirement (B3) theo chuẩn usecase spec

> Nguồn: `.prompts/skills/write-usecase-spec.md` của agentic-storefront, bản `main @ 0e65bece6` (2026-11-02). File này rút gọn chuẩn đó cho **một lần thay đổi** ở B3; phần Overview và sơ đồ User journey chỉ áp khi xuất file `Usecase_<Module>.md` mới (mục 9); cluster của tenant, History và ID ổn định sau merge thuộc việc cập nhật spec đã có, làm theo chuẩn gốc (mục 9 không ghi đè file đã có). Plugin thêm giá trị Scope `Change` (mục 3) cho yêu cầu không có issue; chuẩn gốc không có giá trị này. Chuẩn gốc đổi thì cập nhật file này và SHA ở trên. Bản trong plugin 3.3.1 lấy từ `src/backend/bff/plugins` trên `main @ 9d8a126c4` (commit thêm file: `b87b23773`), chỉnh tên bước theo quy trình B0–B6 + B2.5.

Bảng là yêu cầu viết từ góc nhìn PO: không nêu intent, API, mã lỗi, tên file hay code. Dev ánh xạ case vào hệ thống; case nào không ánh xạ được thì quay lại thành câu hỏi.

## 1. Cột và ngôn ngữ

9 cột, đúng thứ tự (script `work_item_state.py` từ chối nếu sai):

`ID | Scope | Trigger | Điều kiện trước | Chat panel | Display panel | Hệ thống | Không được làm | Pass rate`

Script nhận cả tên cột tiếng Anh (`Precondition`, `System`, `Must not`); trong file này hai cách gọi là một.

- ID, giá trị Scope và Pass rate giữ tiếng Anh. Nội dung ô viết bằng ngôn ngữ làm việc của tenant; lời khách, tên sản phẩm giữ nguyên.
- Label theo một cột duy nhất của bảng dưới, không trộn:

| Label | Tiếng Việt | English |
|---|---|---|
| Khách gõ | `[Chat]` | `[Chat]` |
| Bấm trên Display panel | `[Bấm · Display]` | `[Display click]` |
| Bấm trong chat, hệ thống xử lý | `[Bấm · Chat]` | `[Chat click]` |
| Bấm trong chat, gửi cho AI thành một câu | `[Chip · AI]` | `[Chat chip]` |
| Sự kiện hệ thống | `[Hệ thống]` | `[System]` |
| Cột không áp dụng | `Không bắt buộc ...` | `Not required ...` |
| AI không được trả lời | `Không có câu chat.` | `No chat reply.` |
| Cùng nội dung case khác | `Như <ID>` / `Như <ID>, thêm: ...` | `Same as <ID>` / `Same as <ID>, plus: ...` |
| Phải xảy ra sau case khác | `Sau <ID>` | `After <ID>` |
| Khách gõ khi AI đang hỏi lại | `[Chat] Khách trả lời "..." khi AI hỏi ...` | `[Chat] Customer replies "..." when AI asks ...` |

## 2. Thuật ngữ

- **usecase**: một cách bắt đầu một intent: một tập câu nói mà câu nào cũng khớp mọi case của nó, hoặc một nút, một chip, một sự kiện hệ thống.
- **case**: một dòng của bảng: usecase dưới một trạng thái dữ liệu (giỏ rỗng, hai laptop, đã áp mã, chưa đăng nhập...).
- **chip**: nút lựa chọn ngắn AI hiện trong chat. **card**: khung AI hiện trong chat cho một sản phẩm / món / khuyến mãi, có nút riêng; gọi theo thứ nó hiển thị ("thẻ khuyến mãi").
- **wait point**: case mà AI giữ một lệnh ghi lại cho tới khi khách trả lời (hỏi món nào, hỏi xác nhận, đưa lựa chọn).
- **reference case**: case viết đầy đủ một kết quả dùng chung; case khác trỏ tới bằng `Như <ID>`.
- **pending case**: case viết theo phương án mặc định trong lúc còn câu hỏi mở gửi người khác ngoài PO; đánh dấu ⏳.

## 3. Trường cố định

- **ID**: `<MODULE>-<FAMILY>-<nnn><X>`, ví dụ `CART-DEL-017C`. `<FAMILY>`: mã ngắn của nhóm intent (`VIEW`, `ADD`, `DEL`...); `<nnn>`: một dãy số chung cho cả bảng, không đếm lại theo nhóm, không hai usecase chung số; `<X>`: chữ cái của case (bỏ khi usecase chỉ có một case). Bảng chưa lưu lần nào: số chạy 001, 002... từ trên xuống, không hụt; thêm / xoá dòng thì đánh lại. Từ lần lưu Requirement đầu tiên (`save_requirement`), ID cố định như spec đã có trên `main`: sửa ô / đổi thứ tự giữ ID cũ; usecase mới lấy số lớn nhất đã lưu (tính cả ID đã xoá) cộng một; case mới của usecase đã có lấy chữ cái kế tiếp; dòng bỏ thì xoá, ID đó không dùng lại; áp cả khi sửa Requirement cũ và bản thay thế (`supersedesId`). ID không trùng và quy tắc giữ ID (script kiểm, `SKILL.md` mục B3 / B0 resume).
- **Scope**: `issue <số>` (không viết `#<số>`) khi yêu cầu có issue; `Change` khi yêu cầu không có issue (thường gặp với Staff tenant), nghĩa là thuộc lần thay đổi này; `Proposed` (ngoài lần thay đổi này, chưa có issue, cần issue cải tiến) hoặc `Deferred post-MVP` (issue hoãn tường minh). Không bịa số issue; B1 không có số issue thì dùng `Change`. Chỉ dòng `issue <số>` / `Change` được làm và được kiểm ở Handoff. Thêm 🔒 khi case giữ một ràng buộc cứng của issue; thêm `⏳ <OQ-ID>` khi pending, chỉ cho dòng `issue <số>` / `Change`.
- **Trigger**: bắt đầu bằng channel tag (script kiểm). Dòng đi theo một mũi tên của mockup ghi thêm `(T<n>)` của transition đó; mỗi transition có ít nhất một dòng (script kiểm). Case quy tắc bắt phải có mà mockup không vẽ (rỗng, nhiều món, câu hỏi thông tin, nhánh wait point) không gắn `(T<n>)`; chat/mockup chưa nói về nó thì viết theo phương án mặc định ở mục 7 và liệt kê dưới bảng thành giả định để người dùng duyệt. Mọi câu nói của một usecase nằm trong Trigger; điều phân biệt các case đặt ở Precondition. Câu trả lời gõ tay cho wait point trích lời khách rồi nêu câu hỏi nó trả lời; không mô tả thay ("khách đồng ý").
- Bảng markdown không gộp ô: các case của một usecase lặp lại cùng Trigger ở mỗi dòng.

## 4. Quy tắc case

- **R1 Trigger test.** Mọi câu nói trong Trigger phải khớp mọi case; câu chỉ khớp một case thì mở usecase riêng. Mỗi nút, chip, sự kiện hệ thống là một usecase riêng (trừ gộp `[Chat]` + `[Chip · AI]` ở R2). Cùng câu ngắn ("ừ", "thôi") sau các wait point khác nhau là usecase khác nhau. Case cần hơn năm dòng Must not thì tách.
- **R2 Tách hay gộp.** Tách khi đường xử lý khác: đọc hay ghi, hỏi lại hay làm ngay, màn hình khác, dữ liệu sau đó khác, channel khác. `[Chat]` và `[Chip · AI]` dùng chung usecase khi mọi ô giống nhau. Lần bấm do hệ thống xử lý (`[Bấm · Display]`, `[Bấm · Chat]`) giữ usecase riêng, đặt cạnh usecase chat cùng intent và trỏ `Như <ID>` ô nào khớp. Chỉ khác câu chữ thì gộp vào Trigger; sai chính tả, không dấu, teencode không thành dòng mới.
- **R3 Thất bại và từ chối** có case riêng, ngay dưới case thành công, khi kết quả khác.
- **R4 Thông tin vs hành động.** Câu hỏi không ghi gì và lệnh có ghi là usecase riêng. Trả lời thông tin: đủ → trả lời; một phần → trả lời phần đó và nói phần còn lại ở đâu; không có → nói vậy và chỉ kênh tự phục vụ.
- **R5 Persona vs dòng.** Giọng điệu và bẫy chung (đặt hàng thay khách, bịa giá, xin số tài khoản, hứa thời gian giao) thuộc Persona; chỉ thành case khi bước này phải làm một việc cụ thể.
- **Trạng thái dữ liệu.** Mỗi usecase có một case cho mỗi trạng thái làm kết quả khác: chưa có gì, đúng một, nhiều, có cái không dùng được (hết hàng, hết hạn), đã chọn từ trước, chưa đăng nhập, lỗi hệ thống. Lệnh không nêu rõ đối tượng cần đủ ba case: không có → báo khách; đúng một → làm luôn (trừ khi đã chốt phải xác nhận); nhiều → hỏi khách chọn.
- **R10 Không mô tả UI tĩnh.** Không viết vị trí, màu, cỡ chữ. Chỉ viết điều QC quan sát được: nút tồn tại, dòng biến mất, tổng thay đổi.
- **R11 Wait point có bốn nhánh:** (1) câu trả lời đúng, mỗi channel khách trả lời được là một usecase; (2) yêu cầu khác trong lúc AI chờ, tách câu hỏi không ghi và lệnh ghi mới; (3) thao tác trên Display panel trong lúc chờ, tách thao tác hoàn tất / làm mất hiệu lực yêu cầu đang chờ và thao tác để nó còn hiệu lực; (4) câu trả lời vẫn chưa rõ. Hỏi lại thông tin còn thiếu mà không giữ lệnh ghi nào thì không phải wait point.
- **R12 Chip và card.** Mọi chip và nút card AI đưa ra được nêu tên in đậm trong Chat panel của case hiển thị nó; bấm vào là usecase riêng. Chip nêu rõ hành động và đối tượng ("Gỡ mã ABC", "Xoá hẳn"); không đưa chip chỉ dẫn tới một câu hỏi khác. Case AI hỏi lại có dòng Must not cấm đoán món / mã (trừ khi khách giao hệ thống chọn); bấm chip đại diện một món trong nhiều món có dòng Must not cấm tác động món khác.
- **R13 Chat và màn hình.** Mọi hành động màn hình làm được cũng yêu cầu được bằng chat, cùng kết quả. Nút trong chat và control trên màn hình của cùng hành động cho cùng lệnh ghi và cùng dữ liệu trên cả hai panel; control bị vô hiệu thì nút trong chat cũng không làm. Bấm cả hai nút liên tiếp: lần sau theo dữ liệu thật lúc bấm và không làm lại một hành động đã xong (trong chat, AI nói việc đã xong rồi; trên màn, không ghi lại gì); riêng thêm thì thêm lần nữa và checkbox thì đảo trạng thái; lần bấm trong lúc lần đầu còn đang xử lý thì bị bỏ qua, không xếp hàng chờ; tin nhắn gõ trong khoảng đó theo case riêng của nó.

## 5. Viết ô

- **Precondition**: chỉ dữ kiện làm đổi kết quả (đang tick gì, mã nào đã áp, đăng nhập, tồn kho). Không ghi giá hay tổng; không trỏ bảng mẫu. Case sau wait point nói bằng lời điều đã xảy ra và AI đang chờ gì, rồi `(Sau <ID>)`, rồi phần khác biệt. Ô chỉ ghi `Sau <ID>` mà không nói trạng thái bị script từ chối.
- **Chat panel**: liệt kê nội dung phải có, không viết câu nguyên văn (trừ câu cố định như thông báo lỗi chính xác). Câu trả lời hoặc bắt buộc, hoặc `Không có câu chat.`; không bao giờ "tuỳ chọn". Chip và card trong chat thuộc Chat panel.
- **Display panel**: phần tử quan sát được và thay đổi của nó. Lệnh ghi bằng chat nêu khách thấy màn nào sau đó.
- **System**: đọc hay ghi, ghi gì, dữ liệu sau đó, bằng lời thường ("chỉ đọc", "giỏ thành rỗng", "không tạo đơn").
- **Must not**: mỗi ý một dòng (`<br>`), mỗi dòng thành một test; mọi điều AI phải từ chối là một dòng. Không lặp thành "không ..." trong Chat / Display panel. Case 🔒 ghi ràng buộc cứng thành một dòng Must not.
- Cột không áp dụng ghi `Không bắt buộc ...`, không để trống (script kiểm).
- Tiền và số đếm viết "giá trị hệ thống trả về", không ghi cứng.
- **Mỗi case một kỳ vọng**: không viết "nếu X ... ngược lại ...", "nếu có", "nếu cần" về dữ kiện chưa chốt; tách case theo Precondition hoặc chốt theo mục 7.
- **Reference case**: kết quả dùng chung viết đầy đủ một lần; ô khớp ghi `Như <ID>`, khớp nhưng có thêm ghi `Như <ID>, thêm: ...`; luôn trỏ tới ô viết đầy đủ, không trỏ tới ô cũng ghi `Như`.
- Điều phải xảy ra viết thành bắt buộc; chỉ nêu cách trình bày (chip có tên món, card có nút xoá) khi PO đã chọn.

## 6. Pass rate

| Pass rate | Áp dụng | Pass khi |
|---|---|---|
| **100%** | `[Bấm · Display]`, `[Bấm · Chat]`, `[Hệ thống]`; `[Chip · AI]`; `[Chat]` câu rõ ràng có đúng một câu trả lời đúng (xem / hỏi về giỏ hay đơn của chính khách, hỏi chính sách / sản phẩm / giao hàng, lệnh nêu rõ đối tượng hoặc chỉ có đúng một đối tượng, yêu cầu AI phải từ chối) | Bấm / hệ thống: chạy 1 lần, đúng. `[Chat]`, `[Chip · AI]`: chạy 5 lần, mọi ý bắt buộc có ở cả 5. Không lần nào vi phạm Must not |
| **80%** | Chỉ `[Chat]` AI phải phán đoán: không rõ / thiếu thông tin nên phải hỏi lại, nhiều yêu cầu trong một câu, tư vấn / so sánh có nhiều gợi ý đúng | Chạy 5 lần, mọi ý có ở ít nhất 4. Lần trượt chỉ được là hỏi lại vụng hoặc thiếu một ý. Không lần nào đoán rồi làm, nêu sai dữ kiện, vi phạm Must not |

- Một lần chạy pass khi đủ mọi ý của Chat panel, Display panel, System và mọi Shared rule áp cho case.
- Không chấm hình thức (số câu, dấu câu, cách diễn đạt). Trượt: trả lời không đúng ngôn ngữ tenant, lộ câu hệ thống gửi AI, tên kỹ thuật, markdown thô; lệnh ghi sai; con số trong chat khác Display panel (kể cả làm tròn).
- Khó xếp mức cho dòng `[Chat]`: người đọc câu đó có biết chính xác khách muốn gì không? Có → 100%.
- Bấm trong chat: `[Bấm · Chat]` khi hệ thống xử lý trực tiếp; `[Chip · AI]` khi gửi một câu cho AI. Nút đang thiết kế mới thì người dùng (PO) chọn đường đi, hỏi trong lượt B2.5 (mục 7): `[Bấm · Chat]` cho nút làm một hành động cố định (**Xoá hẳn**, **Thanh toán**), `[Chip · AI]` khi AI phải tìm, tư vấn hoặc soạn câu trả lời. Chỉ khi đường đi bị cố định bởi thứ PO không thấy được (Dev, API) mới ghi `[Chip · AI]` (test chặt hơn) kèm ⏳ câu hỏi Dev.
- Script chỉ nhận `100%` hoặc `80%`; `80%` chỉ cho dòng `[Chat]` không gộp `[Chip · AI]` / `[Chat chip]` (usecase gộp ở R2 dùng chung Pass rate, chip luôn 100%).

**Shared rules** (in dưới bảng, chỉ khi có): quy tắc mà case ở nhiều nhóm được chấm theo, QC kiểm được trên một lần chạy, nêu rõ áp cho case nào, và chưa nằm trong Must not hay `Như <ID>` của các case đó. Hay gặp: cặp nút chat / màn hình cùng hành động (R13); lượt hỏi lại chỉ đưa chip trả lời câu hỏi của nó (R12); câu phía khách khi bấm chip / nút card trong chat là đúng chữ trên chip, hoặc "<chữ trên nút> - <tên trên card>".

## 7. Câu hỏi khi thiếu thông tin

- Câu PO tự quyết được (hành vi sản phẩm, câu chữ, flow, bước xác nhận, đường đi của nút trong chat, scope trong issue hoặc lần thay đổi): hỏi trong lượt B2.5 (tối đa 5 câu, theo Khung hỏi), ghi câu trả lời vào case. Câu phát sinh sau B2.5 mà PO tự quyết được: ghi thành giả định dưới bảng, không mở lượt hỏi mới.
- Câu chỉ người khác trả lời được (Dev, đội API / service, chính sách tenant, chủ issue khác): viết case theo phương án mặc định, thêm `⏳ OQ-<MODULE>-<nnn>` vào Scope (chỉ dòng `issue <số>` / `Change`; dòng `Proposed` / `Deferred post-MVP` không mang ⏳). Mặc định chọn theo thứ tự: điều issue nói → điều bản build đang chạy làm → phương án an toàn, dễ đảo ngược nhất (không ghi gì, không làm mất gì của khách).
- In dưới bảng một bảng câu hỏi mở: `ID | Cases | Question | Default in spec | Other options | Current code behavior | Ask | Blocks build | Answer`. Không có câu nào thì bỏ.

## 8. Tự kiểm trước khi in bảng

- [ ] Mọi mục R của B2.5 có ít nhất một ID trong ma trận phủ, hoặc nằm trong "Chưa phủ" kèm lý do (script kiểm).
- [ ] Dòng `[Chat]` câu rõ ràng, nêu đúng đối tượng (một món, một mã) ghi 100%, không 80% (mục 6).

- [ ] 9 cột đúng thứ tự; không ô trống; ID không trùng; bảng chưa lưu thì số chạy không hụt, bảng đã lưu thì giữ ID cũ (mục ID).
- [ ] Mọi Trigger có channel tag; dòng theo mũi tên mockup có `(T<n>)`, đủ mọi transition; case mặc định ngoài mockup đã liệt kê dưới bảng thành giả định.
- [ ] Mọi nút, chip, nút card, sự kiện hệ thống trong mockup có usecase.
- [ ] Mọi usecase bắt đầu được khi chưa có gì có case rỗng; lệnh không nêu đối tượng có đủ ba case.
- [ ] Mọi wait point đủ bốn nhánh (R11).
- [ ] Mọi chip / card nêu tên trong Chat panel và có usecase riêng; Must not đủ theo R12.
- [ ] Mọi lệnh ghi bằng chat nêu màn hình sau đó; mọi lần bấm nêu câu trả lời chat hoặc `Không có câu chat.`.
- [ ] Không "nếu X ... ngược lại ..."; mọi `Như` / `Sau` trỏ tới case có thật.
- [ ] Không intent, API, mã lỗi, tên file, con số ghi cứng, mô tả UI tĩnh; không dòng chỉ là giọng điệu chung.
- [ ] Scope đúng mục 3 (không bịa số issue; không có issue thì `Change`); Pass rate đúng mục 6; câu hỏi mở có ⏳ khớp bảng câu hỏi.

## 9. Xuất file `Usecase_<Module>.md` (khi người dùng yêu cầu)

Chỉ khi người dùng nói "xuất usecase spec" (hoặc tương đương) sau khi bảng đã **Xác nhận**:

Chỉ dùng nội dung trong file này; không đọc file ngoài plugin.

Bố cục, không thêm mục khác:

1. `# Usecase <Module> - <tên bước> (Shopper - <Tenant>)`, rồi một câu: các usecase của bước, từ điểm bắt đầu đến điểm kết thúc; thêm "Các dòng có 🔒 là ràng buộc cứng từ issue <số>." và, khi có case pending, "Các dòng có ⏳ theo phương án mặc định trong lúc câu hỏi ghi cạnh dấu còn mở."
2. `**Quy tắc chấm điểm**`: chép bảng và các gạch đầu dòng của mục 6, thay ví dụ bằng ví dụ của bước.
3. `**Quy định chung**`: Shared rules (bỏ khi không có).
4. `## 1. Overview`: bảng `Cluster | Group | Description | Usecase` (số usecase mỗi group, dòng `Tổng`), rồi `**Hành trình khách**` là một sơ đồ Mermaid flowchart: mỗi chặng một khung có tên, xếp từ trên xuống; mỗi bước một ô có số bước, tên, số group và một dòng ngắn khách làm gì; mũi tên có nhãn là việc khách làm; chỉ vẽ nhánh đưa khách sang chỗ khác (rỗng, lỗi, quay về bước trước); không ghi case ID; label không bắt đầu bằng "1. " (viết "1 · Tên"), không dùng `#`.
5. `## 2. Details`: `### A. <Cluster>` → `#### A.1 <Group>` → bảng HTML 9 cột như bảng B3; các case của một usecase gộp ô Trigger bằng `rowspan`; trong ô chỉ dùng `<b>`, `<code>`, `<br>`; mỗi `<tr>` một dòng. Cluster mặc định cho bán lẻ: Quản lý <đối tượng của bước> · Sản phẩm & tìm kiếm · Khuyến mãi · Giao hàng · Thanh toán & đơn hàng · Bảo hành, đổi trả & dịch vụ · Tình huống khó.
6. Bảng câu hỏi mở (mục 7) ghi ra file riêng `open-questions.md` cạnh spec, chỉ khi còn câu hỏi.

Quy tắc khi xuất:

- Dữ liệu lấy từ bảng đã xác nhận; không thêm case mới chưa được xác nhận (muốn thêm thì quay lại B3).
- Giữ nguyên ID của bảng B3.
- Ghi file vào thư mục làm việc của người dùng (đường dẫn hỏi một lần); không ghi lên hệ thống, không gọi MCP write. Đường dẫn mặc định: có thư mục `tenants/<tenant>/docs/<module>/` (chạy trong repo agentic-storefront) thì dùng `tenants/<tenant>/docs/<module>/Usecase_<Module>.md`; không có thì `docs/<module>/Usecase_<Module>.md`. Trước khi hỏi, liệt kê tên các file `Usecase_*.md` đã có trong thư mục đó (chỉ tên, không đọc nội dung); có file thì báo tên để người dùng chọn cập nhật file đó theo dòng dưới, không tạo file mới cạnh nó.
- File đích đã tồn tại (chỉ kiểm đường dẫn, không đọc nội dung): không ghi, không tạo bản song song. Báo người dùng spec của module đã có và cần cập nhật spec đó theo `.prompts/skills/write-usecase-spec.md` (giữ ID cũ; usecase mới lấy số lớn nhất trong spec và History cộng một; ID bị bỏ ghi vào History), vì ID của bảng B3 chạy lại từ 001 sẽ trùng ID đang có và làm test QC trích sai case.
- Dòng `Change`: người dùng cho số issue thì đổi thành `issue <số>`; không có thì giữ `Change` và báo người dùng giá trị này lệch chuẩn gốc, cần gắn issue trước khi đưa spec vào repo.
- Báo người dùng: đây là bản theo quy tắc rút gọn của plugin; muốn đủ chuẩn (thứ tự cluster của tenant) thì đối chiếu chuẩn usecase spec của dự án.
