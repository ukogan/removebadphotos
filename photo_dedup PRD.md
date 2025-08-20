## Desire

My photo library is full of a series of photos that I took, for example, on a hike, or of my kids, where the first photos ended up being supplanted in quality by later photos. I start taking a sequence of photos until I'm happy with the results, but then I never go back and delete the previous ones. Or in the case of photos of people, I may take a bunch of photos in the hopes that my kids are both smiling in one of them, for example. I would like to clear my photo library of photos that are the not-best ones of a series, and I'm wondering if there are already public repositories on GitHub or elsewhere that exist with that exact purpose. My goal is to use this on photos in the Mac OS or iCloud photo library, and also potentially in the Google photo library, which actually syncs between the two. One of the other problems I have is if I delete something from the Google photo library, it doesn't delete it from the Mac photo library. Or maybe it's the other way around. Once it syncs to Google, it doesn't delete in Google if I've deleted it in Mac, so I end up having over-storage in two places. So I'd like to find or build a tool that can solve this problem in a way where it will find very similar photos and say, Hey, here are the 5 or 10 or 20 photos that look very similar because they were taken within a short period of time, the subjects are similar, and perhaps in a future version even suggests to me which one might be the best. So sometimes it's going to be the last one, sometimes it's going to be one in the middle that was either sharper or better composed or where the subjects, if they're people, were smiling and looking at the camera and so forth. And I'd like to have a way to be able to quickly review sets of photos like this and ideally even sort them from the largest sets in terms of storage to the smallest so that I can quickly reduce the size of my photo library. Another potential future enhancement of the approach might be to make it like a little game that gives me a handful of such examples every day or every time I play so that over time I can gradually bring the photo library under control.

##Response
You’re raising a familiar and important pain point—being stuck with multiple near-duplicate or burst photos of the same moment and struggling with syncing/deletion inconsistencies between Mac/iCloud and Google Photos. You’re thinking proactively about automating the cleanup process, perhaps even gamifying it over time. Smart!

Here’s a breakdown of what’s already available, along with ideas for tooling you could adapt or build — plus some workflow strategies to align your libraries across platforms more reliably.

⸻

Existing Tools & GitHub Projects

Google Photos Deduper

A local web app + Chrome extension for detecting/removing duplicate images in Google Photos. Unfortunately, due to Google API changes, it stopped working as of March 31, 2025 ￼ ￼.

difPy – Duplicate Image Finder (Python)

A Python package that compares images based on their visual content (not just hashes), identifies duplicates or similar images, and flags lower-resolution versions for deletion. You can use it to safely review and remove redundant shots ￼.

Philipbl’s Duplicate-Images Python Script

Uses perceptual hashing (pHash) to fingerprint and compare images, helping locate truly similar ones. Offers a manual review mode so you can decide which to trash ￼.

PowerPhotos (Paid macOS App)

Highly recommended for Photos/iCloud library cleanup. Lets you combine libraries, detect duplicates, and define rules—e.g., favor HEIC or edited versions—before culling. Safe and powerful ￼.

OSXPhotos (Python CLI)

A command-line utility for manipulating Photos libraries on macOS. Great for scripting tasks like batch-editing titles to preserve the chronological order of bursts in your library ￼.

⸻

Insights from Other Users

From a Reddit thread on similar-photo detection:

“The issue with the many 3rd party apps I’ve tried is that they need the photos to be on my desktop and they are in the cloud (Google Photos).” ￼

You’re not alone in encountering issues with cloud-stored photos and limitations of current tools.

⸻

macOS Photos (Built-In) Limitations
	•	Burst selection: You can manually choose a best shot via “Make a Selection…” within a burst in the Photos app ￼.
	•	Duplicate merging: Apple’s built-in duplicate finder often chooses the newer or lower-quality version—regardless of resolution—so it’s not always reliable for preserving the best image ￼.

⸻

Summary Table: Tools & Features

Tool / Method	Platform	Key Strengths	Limitations / Notes
PowerPhotos	macOS (Photos)	Guided duplicate cleanup, metadata‑aware selection	Paid, but safe and robust ￼
difPy	Python	Visual similarity, flags lower-res duplicates	Command-line; manual review needed ￼
pHash script (philipbl)	Python	Perceptual hashing; fingerprint-based detection	Also command-line, manual cull ￼
OSXPhotos	Python/macOS	Batch metadata editing (e.g. filenames to titles)	Works alongside Photos; more of a helper tool ￼
Google Deduper	Web + Chrome	Originally targetted Google Photos duplicates removal	Broken as of March 2025 due to API changes ￼


⸻

Recommended Workflow Strategy
	1.	Backup Everything First
Always duplicate your libraries before major operations (Time Machine, external drive, or archive library).
	2.	Consolidate in Photos/macOS
Use PowerPhotos to gather all photos—whether in separate libraries, iCloud, or imported from Google—into a master library. You can clean duplicates and apply smart rules (e.g., prefer edited, HEIC, or larger file size).
	3.	Name Burst Photos Logically
With OSXPhotos, batch-assign titles from filenames (e.g., timestamped sequence names). This lets you sort bursts precisely and pick the best shot faster ￼ ￼ ￼.
	4.	Detect Similar/Duplicates for Large Sets
Export suspect sequences (e.g., hiking bursts) to a folder and run difPy or the pHash script to identify similar sets. Then manually review and pick top images before deleting the rest ￼.
	5.	Sync Cleaned Library
After culling, let iCloud sync propagate deletions. To mirror in Google Photos, avoid re-uploading everything blindly. Use Google’s web UI or Backup & Sync with cautious selections.
	6.	Optional “Daily Game” Approach
Build a small script that:
	•	Picks a random burst/similar group
	•	Presents it for quick “best-shot” selection
	•	Moves others to a review or deletion queue—it’d feel like a mini game. You could wrap this around difPy or your own fingerprint logic.

⸻

GitHub Integration Ideas for Your Tool
	•	Use difPy for detecting similarity.
	•	Add metadata analysis: Use image sharpness, faces, smiles detection (via OpenCV or ML models) to rank “best” shots.
	•	UI or TUI: Let the user “star” best shot and auto-queue the rest for deletion.
	•	Cross-library syncing: Wrap Photos Library and Google Photos APIs to reconcile deletions across ecosystems.

⸻

Final Thoughts
	•	PowerPhotos is your best single-pane solution for Photos/macOS library cleanup.
	•	For more custom workflows, combine difPy, philipbl’s pHash script, and OSXPhotos to build powerful pipelines.
	•	Automating or gamifying the process is totally feasible—start small with CLI or a lightweight UI script.

## Constraints:
Start with local photos in MacOS photos, no videos. To keep it simple let's make some constraints:
* all photos taken with 10 seconds of the photo before and After
* all photos taken with the same camera
* similar composition

## architectural constraints
* no commercial tools, only open source libraries

User starts app / website / script
Flow:
* all photos that meet the conditions should be presented as sets side by side each other (no more than 4 in a group) with key metadata under each one (timestamp, size).
* app preselects by highlighting the border of the photo it thinks is the best of the group; if the user wants to save more than one, or change the one that is saved, they simply click to highlight the photo(s) they want to keep
* the app generates a list of files for deletion
* user confirms they want to proceed
* app runs a script to tag all the rejected photos (those not selected) as "marked-for-deletion" and adds them to a smart album for that session named "marked for deletion on MMM-DD at HH:MM to save ### MB" or similar . it also generates a list of the photos and key identifying metadata and tells the user the total memory saved if they proceed with deletion.
* user manuall deletes photos in that album in the MacOS photos app directly
* we can handle deletion in Google photos later but the shot list generated by the script should help to search and delete photos via api