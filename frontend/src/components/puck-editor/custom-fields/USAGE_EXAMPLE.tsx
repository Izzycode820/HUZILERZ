/**
 * USAGE EXAMPLE: How to use custom fields in puck.config.tsx
 *
 * Copy these examples into your theme's puck.config.tsx file
 */

import type { Config } from "@measured/puck";
import { TextField, ColorPicker, Toggle, Slider, Spacing, ImagePicker } from "@/components/puck-editor/custom-fields";

export const exampleConfig: Config = {
  components: {
    HeroSection: {
      label: "Hero Section",
      fields: {
        // ✅ Enhanced Text Field (with bold/italic/underline toolbar)
        description: {
          type: "custom",
          label: "Description",
          render: ({ value, onChange }) => (
            <TextField value={value} onChange={onChange} />
          ),
        },

        // ✅ Color Picker (visual color selector)
        backgroundColor: {
          type: "custom",
          label: "Background Color",
          render: ({ value, onChange }) => (
            <ColorPicker value={value} onChange={onChange} />
          ),
        },

        // ✅ Toggle Switch (better than checkbox)
        autoplay: {
          type: "custom",
          label: "Autoplay",
          render: ({ value, onChange }) => (
            <Toggle
              value={value}
              onChange={onChange}
              label="Enable autoplay"
              description="Video will play automatically"
            />
          ),
        },

        // ✅ Slider (for numbers like opacity, font size)
        opacity: {
          type: "custom",
          label: "Opacity",
          render: ({ value, onChange }) => (
            <Slider
              value={value}
              onChange={onChange}
              min={0}
              max={100}
              step={1}
              unit="%"
            />
          ),
        },

        // ✅ Spacing Control (padding/margin box model)
        padding: {
          type: "custom",
          label: "Padding",
          render: ({ value, onChange }) => (
            <Spacing
              value={value || { top: 0, right: 0, bottom: 0, left: 0 }}
              onChange={onChange}
              unit="px"
            />
          ),
        },

        // ✅ Image Picker (opens media library modal)
        backgroundImage: {
          type: "custom",
          label: "Background Image",
          render: ({ value, onChange }) => (
            <ImagePicker value={value} onChange={onChange} />
          ),
        },
      },
      defaultProps: {
        description: "Welcome to our store",
        backgroundColor: "#ffffff",
        autoplay: false,
        opacity: 100,
        padding: { top: 20, right: 20, bottom: 20, left: 20 },
        backgroundImage: "",
      },
      render: ({ description, backgroundColor, autoplay, opacity, padding, backgroundImage }) => (
        <div
          style={{
            backgroundColor,
            opacity: opacity / 100,
            padding: `${padding.top}px ${padding.right}px ${padding.bottom}px ${padding.left}px`,
            backgroundImage: backgroundImage ? `url(${backgroundImage})` : undefined,
          }}
        >
          <div dangerouslySetInnerHTML={{ __html: description }} />
        </div>
      ),
    },
  },
};

/**
 * TIPS:
 *
 * 1. TextField: Use for descriptions, headlines with formatting
 * 2. ColorPicker: Use for colors (background, text, borders)
 * 3. Toggle: Use for boolean values (show/hide, enable/disable)
 * 4. Slider: Use for numeric values with range (0-100, 10-50, etc.)
 * 5. Spacing: Use for padding/margin CSS properties
 * 6. ImagePicker: Use for any image URL field
 */
