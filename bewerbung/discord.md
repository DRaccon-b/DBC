Hey Gorjie! 👋

I'm **Bauzel**. I really love what you're building with **Digimmo**, and I'd like to help make it even better. I'm offering to make **maps for the project, completely free**. No payment needed, I just want Digimmo to look as good as possible.

**What I've already built** (16×16 tiles, top-down, animated):
• Forest map with river, waterfall & beach (110×120)
• Factorial Town: industrial town & reactor
• Server Desert: dunes & buried arena
• Gear Savanna: canyon & plateaus
• Freezeland: ice cliffs & frozen lake

Water, wind, campfires, lanterns and snow are all animated. Every object sits exactly on the 16×16 grid.

**How the layers work** (1st picture, left → right = draw order)
1️⃣ **Ground**: everything *below* the player, incl. the feet of trees and lamps
2️⃣ **Collision**: data only, per tile: `1` walkable, `2` blocked, `3` walkable but hides the player
3️⃣ **Player / NPCs**
4️⃣ **Overlay**: everything *above* the player (tree crowns, lamp heads, roofs)
➡️ The player can walk *behind* a tree, while the trunk still blocks the way.

**Editor idea** (2nd picture)
🟥 **Block**: paint walkable / blocked / walk-behind straight onto the map
🔼🔽 **Layer up / down**: select an object and move it above or below the player
✂️ **Split at foot**: the foot blocks its tile, the top goes on the overlay
📦 **Export**: `ground.png`, `overlay.png`, `collision.json`, easy to load in any engine

That way small fixes can be done without me.

Happy to send you full-res maps, GIFs, or build a test map in your style first. Thanks for all the work you put into Digimmo! 🙌

– Bauzel
