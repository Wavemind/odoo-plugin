/* @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import { loadWysiwygFromTextarea } from "@web_editor/js/frontend/loadWysiwygFromTextarea";


publicWidget.registry.TaskWysiwygWidget = publicWidget.Widget.extend({
  selector: ".offer_head",
  start: async function () {
    var self = this;
    // Initialize the WYSIWYG editor on all text areas with the o_wysiwyg_loader class

    $("textarea.o_wysiwyg_loader")
      .toArray()
      .forEach((textarea) => {
        var $textarea = $(textarea);
        var $form = $textarea.closest("form");

        var options = {
          toolbarTemplate: "website_test.web_editor_toolbar",
          toolbarOptions: {
            showColors: false,
            showFontSize: false,
            showHistory: true,
            showHeading1: false,
            showHeading2: false,
            showHeading3: false,
          },
          resizable: true,
          userGeneratedContent: true,
          height: 200,
        };
        loadWysiwygFromTextarea(self, $textarea[0], options).then((wysiwyg) => {
          $form.on("submit", () => {
            const htmlContent = wysiwyg.getValue();
            $("#description_input").val(htmlContent);
          });
          $form
            .find(".note-editable")
            .find("img.float-start")
            .removeClass("float-start");
        });
      });
    return this._super.apply(this, arguments);
  },
});
