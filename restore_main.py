import re

log_text = r"""
1 from __future__ import annotations
2 
3 import argparse
4 import time
5 import uuid
6 from pathlib import Path
7 
8 from automation.config import STATE_ORDER, STAGE_TO_LAST_STATE, default_settings
9 from automation.logger import configure_logging, get_logger
10 from automation.modules import (
11     altissia,
12     auth_zai,
13     chat,
14     evaluator_groq,
15     extractor,
16     storage,
17     tempmail,
18     vpn,
19 )
20 from automation.state_store import RunState, save_state
21 
22 
23 def parse_args() -> argparse.Namespace:
24     parser = argparse.ArgumentParser(description="ZAI modular automation orchestrator")
25     parser.add_argument(
26         "--stage",
27         choices=["vpn", "mail", "chat", "full"],
28         default="full",
29         help="Run only up to a specific stage",
30     )
31     parser.add_argument(
32         "--keep-open",
33         action="store_true",
34         help="Do not close browser at end (placeholder flag for Selenium integration)",
35     )
36     parser.add_argument(
37         "--open",
38         action="store_true",
39         help="Do not close browser at end (placeholder flag for Selenium integration)",
40     )
41     parser.add_argument(
42         "--parallel",
43         type=int,
44         default=3,
45         help="Number of parallel tabs",
46     )
47     parser.add_argument(
48         "--cycles",
49         type=int,
50         default=1,
51         help="Number of generation cycles",
52     )
53     parser.add_argument(
54         "--seed",
55         type=int,
56         default=None,
57         help="Seed for deterministic profile selection",
58     )
59     return parser.parse_args()
60 
61 
62 def _touch_data_files(base_dir: Path) -> None:
63     data_dir = base_dir / "data"
64     data_dir.mkdir(parents=True, exist_ok=True)
65 
66     credentials = data_dir / "credentials.json"
67     if not credentials.exists():
68         credentials.write_text("[]\n", encoding="utf-8")
69 
70     auth_path = data_dir / "openvpn" / "auth.txt"
71     auth_path.parent.mkdir(parents=True, exist_ok=True)
72     if not auth_path.exists():
73         auth_path.write_text("", encoding="utf-8")
74 
75     prompt1 = data_dir / "prompts" / "prompt1.txt"
76     prompt1.parent.mkdir(parents=True, exist_ok=True)
77     full_prompt = data_dir / "prompts" / "full_prompt.txt"
78     if not full_prompt.exists():
79         full_prompt.write_text(
80             "Build a production-ready application output.", encoding="utf-8"
81         )
82 
83     if not prompt1.exists():
84         prompt1.write_text("Create production-ready code output.", encoding="utf-8")
85 
86     prompt2 = data_dir / "prompts" / "prompt2.txt"
87     if not prompt2.exists():
88         prompt2.write_text("Refine and harden the previous output.", encoding="utf-8")
89 
90 
91 def run() -> int:
92     args = parse_args()
93     settings = default_settings()
94     _touch_data_files(settings.base_dir)
95 
96     log_file = settings.logs_dir / f"run-{int(time.time())}.log"
97     configure_logging(log_file)
98     log = get_logger("automation")
99 
100     run_id = str(uuid.uuid4())
101     state = RunState(run_id=run_id)
102 
103     last_state = STAGE_TO_LAST_STATE[args.stage]
104     last_idx = STATE_ORDER.index(last_state)
105 
106     log.info("Starting run_id=%s stage=%s", run_id, args.stage)
107 
108     profiles = []
109     selected_profile = None
110     prompt_one_result = None
111     prompt_two_result = None
112     driver = None
113 
114     try:
115         for idx, state_name in enumerate(STATE_ORDER):
116             state.state = state_name
117             save_state(settings.run_state_path, state)
118             log.info("[%s] Enter", state_name)
119 
120             if state_name == "INIT":
121                 pass
122 
123             elif state_name == "LOAD_OPENVPN_PROFILES":
124                 profiles = vpn.load_profiles(settings.openvpn_profiles_dir)
125                 selected_profile = vpn.pick_profile(profiles, seed=args.seed)
126                 state.metadata["vpn_profile"] = str(selected_profile)
127                 log.info("Randomly selected VPN profile: %s", selected_profile.name)
128 
129             elif state_name == "CONNECT_OPENVPN":
130                 if selected_profile is None:
131                     raise RuntimeError("Profile is not selected")
132                 vpn.ensure_auth_file(
133                     settings.openvpn_auth_path,
134                     settings.openvpn_username,
135                     settings.openvpn_password,
136                 )
137                 
138                 max_retries = 5
139                 connected = False
140                 for attempt in range(max_retries):
141                     try:
142                         conn_info = vpn.connect_vpn(
143                             selected_profile, settings.openvpn_auth_path, state.run_id
144                         )
145                         state.metadata.update(conn_info)
146                         connected = True
147                         break
148                     except vpn.VPNError as e:
149                         log.warning("[CONNECT_OPENVPN] Attempt %d failed: %s", attempt + 1, e)
150                         if attempt < max_retries - 1:
151                             log.info("[CONNECT_OPENVPN] Picking a new profile and retrying...")
152                             selected_profile = vpn.pick_profile(profiles)
153                             state.metadata["vpn_profile"] = str(selected_profile)
154                             log.info("Randomly selected NEW VPN profile: %s", selected_profile.name)
155                 
156                 if not connected:
157                     raise RuntimeError(f"Failed to connect to VPN after {max_retries} attempts.")
158 
159             elif state_name == "VERIFY_PUBLIC_IP":
160                 if "public_ip" not in state.metadata:
161                     raise RuntimeError("Public IP not available after VPN connect")
162 
163             elif state_name == "MAIL_BOOTSTRAP":
164                 from automation.browser import get_browser
165 
166                 if driver is None:
167                     driver = get_browser(proxy_url=state.metadata.get("proxy"))
168                 email = tempmail.get_temp_mail(driver)
169                 username = tempmail.generate_username()
170                 verify_url = tempmail.build_verify_url(
171                     settings.base_token, email, username
172                 )
173                 state.email = email
174                 state.username = username
175                 state.metadata["verify_url"] = verify_url
176 
177                 auth_zai.open_verify_resend(driver, verify_url)
178 
179             elif state_name == "SAVE_CREDENTIALS":
180                 from automation.browser import get_browser
181 
182                 if not state.email or not state.username:
183                     raise RuntimeError("Cannot save credentials without email/username")
184                 if driver is None:
185                     driver = get_browser(proxy_url=state.metadata.get("proxy"))
186                 driver.get("https://cleantempmail.com")
187                 # Wait for email to arrive and click verify
188                 registered = auth_zai.poll_inbox_and_verify(
189                     driver, password=state.email
190                 )
191 
192                 entry = {
193                     **registered,
194                     "run_id": state.run_id,
195                     "vpn_profile": state.metadata.get("vpn_profile"),
196                     "public_ip": state.metadata.get("public_ip"),
197                     "status": "registered",
198                     "preview_urls": state.preview_urls,
199                 }
200                 storage.upsert_credential(settings.credentials_path, entry)
201 
202             elif state_name in (
203                 "CHAT_CYCLE_ONE",
204                 "CHAT_CYCLE_TWO",
205                 "CHAT_CYCLE_THREE",
206                 "CHAT_PARALLEL_GENERATE",
207             ):
208                 from automation.browser import get_browser
209 
210                 if driver is None:
211                     driver = get_browser(proxy_url=state.metadata.get("proxy"))
212 
213                 full_prompt = (settings.prompts_dir / "full_prompt.txt").read_text(
214                     encoding="utf-8"
215                 )
216 
217                 current_prompt = full_prompt
218 
219                 if state_name == "CHAT_PARALLEL_GENERATE":
220                     for cycle in range(args.cycles):
221                         log.info("[%s] Starting cycle %d/%d with %d parallel tabs...", state_name, cycle + 1, args.cycles, args.parallel)
222                         
223                         original_window = driver.current_window_handle
224                         windows = [original_window]
225                         driver.switch_to.window(original_window)
226                         if cycle > 0:
227                             driver.get("https://chat.z.ai/")
228                             time.sleep(2)
229                             
230                         for _ in range(args.parallel - 1):
231                             driver.execute_script("window.open('https://chat.z.ai/', '_blank');")
232                             time.sleep(1)
233                             windows.append(driver.window_handles[-1])
234                         
235                         for i, window in enumerate(windows):
236                             driver.switch_to.window(window)
237                             chat.ensure_agent_mode(driver, settings.js_dir)
238                             log.info("[%s] Attempting generation in tab %d (Cycle %d)...", state_name, i + 1, cycle + 1)
239                             if not chat.start_prompt(driver, current_prompt):
240                                 log.warning("[%s] Failed to start prompt in tab %d.", state_name, i + 1)
241                         
242                         log.info("[%s] Polling %d tabs for completion (Cycle %d)...", state_name, args.parallel, cycle + 1)
243                         finished_tabs = set()
244                         for _ in range(100):
245                             any_still_generating = False
246                             try:
247                                 current_handles = driver.window_handles
248                             except Exception:
249                                 break
250                             
251                             for i, window in enumerate(windows):
252                                 if i in finished_tabs:
253                                     continue
254                                 if window not in current_handles:
255                                     finished_tabs.add(i)
256                                     continue
257                                 
258                                 try:
259                                     driver.switch_to.window(window)
260                                     status, result = chat.check_generation_status(driver)
261                                 except Exception as e:
262                                     log.warning("[%s] Error checking tab %d: %s", state_name, i + 1, e)
263                                     any_still_generating = True
264                                     continue
265                                     
266                                 if status == "GENERATING":
267                                     any_still_generating = True
268                                 elif status == "FINISHED" and result:
269                                     log.info("[%s] Tab %d finished generating!", state_name, i + 1)
270                                     finished_tabs.add(i)
271                                     extracted = extractor.extract_response(
272                                         result.response_html,
273                                         result.response_text,
274                                     )
275                                     
276                                     eval_result = evaluator_groq.evaluate_response(
277                                         extracted.html, extracted.text
278                                     )
279                                     if eval_result.approved:
280                                         preview_url = chat.to_preview_url(result.chat_url)
281                                         if preview_url not in state.preview_urls:
282                                             state.preview_urls.append(preview_url)
283                                             log.info(
284                                                 "[%s] Approved in tab %d! URL: %s",
285                                                 state_name,
286                                                 i + 1,
287                                                 preview_url,
288                                             )
289                                             
290                                             if state.email:
291                                                 storage.upsert_credential(
292                                                     settings.credentials_path,
293                                                     {
294                                                         "email": state.email,
295                                                         "username": state.username,
296                                                         "preview_urls": state.preview_urls,
297                                                         "status": "completed",
298                                                         "run_id": state.run_id,
299                                                     },
300                                                 )
301                                     try:
302                                         if len(driver.window_handles) > 1 and driver.current_window_handle != original_window:
303                                             driver.close()
304                                     except Exception:
305                                         pass
306                                 elif status in ("ERROR", "SANDBOX_LIMIT"):
307                                     log.warning(
308                                         "[%s] Tab %d hit %s. Closing it.",
309                                         state_name,
310                                         i + 1,
311                                         status,
312                                     )
313                                     finished_tabs.add(i)
314                                     try:
315                                         if len(driver.window_handles) > 1 and driver.current_window_handle != original_window:
316                                             driver.close()
317                                     except Exception:
318                                         pass
319                                         
320                             if not any_still_generating:
321                                 break
322                             time.sleep(5)
323                             
324                         if driver.window_handles:
325                             driver.switch_to.window(original_window)
326 
327                 else:
328                     chat.ensure_agent_mode(driver, settings.js_dir)
329                     for attempt in range(settings.eval_max_attempts):
330                         log.info(
331                             "[%s] Attempt %d with prompt length %d",
332                             state_name,
333                             attempt + 1,
334                             len(current_prompt),
335                         )
336 
337                         if not chat.start_prompt(driver, current_prompt):
338                             log.warning(
339                                 "[%s] Failed to start prompt (input not found).",
340                                 state_name,
341                             )
342                             break
343 
344                         status = "GENERATING"
345                         result = None
346                         for _ in range(60):
347                             status, result = chat.check_generation_status(driver)
348                             if status in ("FINISHED", "ERROR", "SANDBOX_LIMIT"):
349                                 break
350                             time.sleep(5)
351 
352                         if status == "SANDBOX_LIMIT":
353                             log.warning(
354                                 "[%s] Sandbox limit reached, retrying...", state_name
355                             )
356                             continue
357 
358                         if status != "FINISHED" or not result:
359                             log.warning(
360                                 "[%s] Generation failed or timed out: %s",
361                                 state_name,
362                                 status,
363                             )
364                             break
365 
366                         extracted = extractor.extract_response(
367                             result.response_html,
368                             result.response_text,
369                         )
370 
371                         eval_result = evaluator_groq.evaluate_response(
372                             extracted.html, extracted.text
373                         )
374                         if eval_result.approved:
375                             preview_url = chat.to_preview_url(result.chat_url)
376                             state.preview_urls.append(preview_url)
377                             log.info(
378                                 "[%s] Approved! Preview URL: %s",
379                                 state_name,
380                                 preview_url,
381                             )
382 
383                             if state.email:
384                                 storage.upsert_credential(
385                                     settings.credentials_path,
386                                     {
387                                         "email": state.email,
388                                         "username": state.username,
389                                         "preview_urls": state.preview_urls,
390                                         "status": "completed",
391                                         "run_id": state.run_id,
392                                     },
393                                 )
394                             break
395                         else:
396                             log.warning(
397                                 "[%s] Attempt %d rejected: %s",
398                                 state_name,
399                                 attempt + 1,
400                                 eval_result.reason,
401                             )
402                             current_prompt = (
403                                 eval_result.repair_prompt or "Please continue."
404                             )
405 
406                     else:
407                         log.error(
408                             "[%s] Failed to get an approved response after %d attempts",
409                             state_name,
410                             settings.eval_max_attempts,
411                         )
412                     # We could raise here or just let it continue to the next cycle
413                     # raise RuntimeError(f"{state_name} failed after max attempts")
414 
415             elif state_name == "FINALIZE":
416                 state.metadata["keep_open"] = "true" if args.keep_open else "false"
417 
418             log.info("[%s] Done", state_name)
419 
420             if idx >= last_idx:
421                 log.info(
422                     "Reached requested stage=%s at state=%s", args.stage, state_name
423                 )
424                 break
425 
426     finally:
427         vpn.cleanup(state.metadata)
428         if getattr(args, "gh", False) and "gh_display" in locals() and locals()["gh_display"]:
429             locals()["gh_display"].stop()
430         if driver is not None and not args.keep_open and not args.open:
431             try:
432                 driver.quit()
433             except Exception as e:
434                 log.warning("Failed to quit browser gracefully: %s", e)
435 
436     if not args.keep_open and not args.open:
437         vpn.cleanup(state.metadata)
438 
439     save_state(settings.run_state_path, state)
440     log.info("Run completed with %d preview url(s)", len(state.preview_urls))
441 
442     if args.open or args.keep_open:
443         log.info(
444             "Browser is kept open. You can paste preview URLs below and press Enter to save."
445         )
446         log.info("Type 'exit' to quit.")
447         import sys
448 
449         while True:
450             try:
451                 print("Link> ", end="", flush=True)
452                 user_input = sys.stdin.readline().strip()
453                 if not user_input or user_input.lower() in ("exit", "quit"):
454                     if user_input.lower() in ("exit", "quit"):
455                         break
456                     continue
457                 if user_input.startswith("http"):
458                     state.preview_urls.append(user_input)
459                     if state.email:
460                         storage.upsert_credential(
461                             settings.credentials_path,
462                             {
463                                 "email": state.email,
464                                 "username": state.username,
465                                 "password": state.email,  # email is used as password
466                                 "preview_urls": state.preview_urls,
467                                 "status": "completed",
468                                 "run_id": state.run_id,
469                                 "vpn_profile": state.metadata.get("vpn_profile"),
470                                 "public_ip": state.metadata.get("public_ip"),
471                             },
472                         )
473                         log.info("Saved link: %s", user_input)
474                     else:
475                         log.warning("No email registered yet. Saved to state only.")
476                 else:
477                     log.info("Ignored non-URL input.")
478             except KeyboardInterrupt:
479                 break
480             except Exception as e:
481                 log.error("Input error: %s", e)
482 
483     if state.preview_urls:
484         log.info(
485             "Saving %d accumulated preview urls to credentials...",
486             len(state.preview_urls),
487         )
488         
489         if state.email:
490             storage.upsert_credential(
491                 settings.credentials_path,
492                 {
493                     "email": state.email,
494                     "username": state.username,
495                     "preview_urls": state.preview_urls,
496                     "status": "completed",
497                     "run_id": state.run_id,
498                 },
499             )
500             
501         log.info("Pushing %d accumulated preview urls to altissiabooster repo...", len(state.preview_urls))
502         altissia.append_and_push_links(state.preview_urls)
503 
504     vpn.cleanup(state.metadata)
505     return 0
506 
507 
508 if __name__ == "__main__":
509     raise SystemExit(run())
"""

lines = [line.split(" ", 1)[1] for line in log_text.strip().split("\n")]
with open("automation/main.py", "w") as f:
    f.write("\n".join(lines) + "\n")
print("Restored main.py cleanly")
