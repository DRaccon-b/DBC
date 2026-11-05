Hey Gorjie! 👋

You've already seen my maps, so I'll keep it short: I'd really like to help out with **Digimmo**. I just want the game to have the best possible look. I'm **not asking for credits, money, or any special treatment**. I'd simply like to contribute.

So two questions:
• Would you like to **integrate my maps into the game**?
• Would you like **more maps**? I'm happy to make more, in whatever style or theme you need.

I also have an idea for a **layer system** (see the pictures, left → right = draw order):
1️⃣ **Ground**: everything below the player, incl. the feet of trees and lamps
2️⃣ **Collision**: one value per tile: walkable / blocked / walkable but hides the player
3️⃣ **Player / NPCs**
4️⃣ **Overlay**: everything above the player (tree crowns, lamp heads, roofs)
➡️ This way the player can walk *behind* a tree, while the trunk still blocks the way.

On top of that, a small **editor** could let you paint blocked tiles directly onto the map and move objects a layer **up or down** (above or below the player). It would export plain `ground.png`, `overlay.png` and `collision.json`.

Do you think something like that could work in Digimmo? Or would it be too much effort, or hurt performance? I'd just like to hear your opinion.

And honestly, if you'd rather say "it's my project and I want to keep doing everything myself", that's **completely fine** with me. No hard feelings at all! 🙂

– Bauzel
