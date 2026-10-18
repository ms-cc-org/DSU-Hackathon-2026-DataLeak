# Generated asset prompts

Higgsfield media is decorative only. It must never be mistaken for data: every number, chart and map
in the app comes from the supplied records.

## Status (Oct 17, 2026)

**No assets have been generated.** The team's Higgsfield account is on the free plan with 1.35 credits:

- Image models (`gpt_image_2_5`, `nano_banana`) returned "Requires basic plan or higher". No credits were spent.
- A 5-second video (`seedance_2_5`) costs 35 credits, above the balance.

The app runs fully without these files: `web/ui.py` shows an asset only if the file exists, and
otherwise renders the page without it.

## Planned assets

Generate in one session and one visual style, save the files to `web/assets/media/` under these
names, and fill in the date, model, settings and a verification note for each.

| File | Where it appears | Planned model | Prompt |
|---|---|---|---|
| `intro_loop.mp4` | Overview header (muted, looping) | `seedance_2_5`, 16:9, 5 s, no audio | Slow aerial drift over an Iowa cornfield in summer; green rows gradually dry to yellow and brown under a dusty orange haze, gentle camera motion, no text |
| `hero_field.jpg` | County risk header | `gpt_image_2_5`, 16:9 | Wide aerial landscape photograph of rolling Iowa farmland in late summer: neat corn rows, the left side lush green, the right side drought-stressed yellow and brown with cracked dry soil between rows, soft hazy late-afternoon light, muted natural colors, documentary photography style, no people, no text, no logos |
| `transition_parched.jpg` | Optional, between Mode 1 and Mode 2 | `gpt_image_2_5`, 16:9 | Close-up of corn plants in a field: healthy green leaves in the foreground fading to curled, dry, brown leaves and cracked soil in the background, shallow depth of field, soft natural daylight, muted natural colors, documentary photography style, no people, no text, no logos |

Keep each file small (images under 500 KB, video under 3 MB) so pages open fast. When files are
added, list them in the README's AI-use disclosure and on the Credits page.
