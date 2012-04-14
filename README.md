Export Selected
===============

A Blender Addon that adds an option to export only selected objects for every
registered exporter. The addon also gives you an option to export the objects
to a separate .blend file.

By default children of the selected objects are exported too (the "Include
Children" option).

For PLY format, all the selected objects would be exported as a single mesh.

Installing
----------

Hit `Ctrl+Alt+u` to load up the User Preferences (I always use the keystroke
for this because of the occasional time where you miss, using the `File` menu,
and click `Save User Settings`). Click the `Install Addon...` button at the
bottom, then navigate to your `io_export_selected.py` script.

Next, and this is a tricky bit, if you're not used to installing Addons: you
have to follow up by checking this little box on the right of the Addon entry
in the list. If, for some reason, you have a hard time finding it, you can
search for `Export Selected` or click on the `Import-Export` button on the
left. Hopefully, though, it comes right up when you do `Install Addon...`.

If you want to keep this addon available at all times, follow the above
steps on a fresh `.blend` (one you `Ctrl+n`d), then hit `Ctrl+u` at this
point. The next time you run Blender you won't have to repeat the above.

When installed, it will add a submenu `Selected` to the Export menu, where
the available formats would be listed.

Contact information
-------------------

(add a link to Blender tracker)

Thanks
------

- rking / Ryan Joseph King - For the original idea and help with the
  repository setup.
