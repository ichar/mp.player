dojo.provide("nong.widget.NongComboBox");
dojo.provide("nong.widget.html.NongComboBox");
dojo.require("dojo.widget.html.ComboBox");
dojo.require("dojo.widget.*");

nong.widget.html.NongComboBox = function(){
    dojo.widget.html.ComboBox.call(this);

    this.size = 30;
    this.id = "";
    this.fadeTime = 50;
    this.searchDelay = 500;
}
dojo.inherits(nong.widget.html.NongComboBox, dojo.widget.html.ComboBox);
dojo.widget.tags.addParseTreeHandler("dojo:nongcombobox");

// implementation
dojo.lang.extend(nong.widget.html.NongComboBox, {
    widgetType: "NongComboBox",
    templatePath: dojo.uri.dojoUri("../nong/widget/templates/NongComboBox.html"),
    templateCssPath: dojo.uri.dojoUri("../nong/widget/templates/NongComboBox.css"),
    inactiveImage: dojo.uri.dojoUri("../nong/widget/templates/combo-arrowdown.gif"),
    activeImage: dojo.uri.dojoUri("../nong/widget/templates/combo-arrowdown-over.gif"),

    arrowActive: function(){
        this._setImage(this.activeImage);
    },

    arrowInactive: function(){
        this._setImage(this.inactiveImage);
    },

    _setImage: function(src){
        this.downArrowNode.src=src;
    },

    fillInTemplate: function(args, frag){
        // FIXME: need to get/assign DOM node names for form participation here.
        this.comboBoxValue.name = this.name+"_selected";
        this.comboBoxSelectionValue.name = this.name;

        // NOTE: this doesn't copy style info inherited from classes;
        // it's just primitive support for direct style setting
        var source = this.getFragNodeRef(frag);
        if ( source.style ){
            // get around opera wich doesnt have cssText, and IE wich bugs on setAttribute
            if(dojo.lang.isUndefined(source.style.cssText)){
                this.domNode.setAttribute("style", source.getAttribute("style"));  
            }else{
                this.domNode.style.cssText = source.style.cssText;
            }
        }

        // FIXME: add logic
        this.dataProvider = new dojo.widget.ComboBoxDataProvider();

        if(!dojo.string.isBlank(this.dataUrl)){
            if("local" == this.mode){
                var _this = this;
                dojo.io.bind({
                    url: this.dataUrl,
                    load: function(type, data, evt){
                        if(type=="load"){
                            if(!dojo.lang.isArray(data)){
                                var arrData = [];
                                for(var key in data){
                                    arrData.push([data[key], key]);
                                }
                                data = arrData;
                            }
                            _this.dataProvider.setData(data);
                        }
                    },
                    mimetype: "text/json"
                });
            }else if("remote" == this.mode){
                this.dataProvider = new dojo.widget.incrementalComboBoxDataProvider(this.dataUrl);
            }
        }else{
            // check to see if we can populate the list from <option> elements
            var node = frag["dojo:"+this.widgetType.toLowerCase()]["nodeRef"];
            if((node)&&(node.nodeName.toLowerCase() == "select")){
                // NOTE: we're not handling <optgroup> here yet
                var opts = node.getElementsByTagName("option");
                var ol = opts.length;
                var data = [];
                for(var x=0; x<ol; x++){
                    data.push([new String(opts[x].innerHTML), new String(opts[x].value)]);
                }
                this.dataProvider.setData(data);
            }
        }

        // Prevent IE bleed-through problem
        this.optionsIframe = new dojo.html.BackgroundIframe(this.optionsListWrapper);
        this.optionsIframe.size([0,0,0,0]);
    },

    hideResultList: function(){
        if(this._result_list_open){
            this._result_list_open = false;
            this.optionsIframe.size([0,0,0,0]);
            dojo.lfx.fadeHide(this.optionsListNode, this.fadeTime).play();
        }
    },

    showResultList: function(){
        // Our dear friend IE doesnt take max-height so we need to calculate that on our own every time
        var childs = this.optionsListNode.childNodes;
        if(childs.length){
            var visibleCount = this.maxListLength;
            if(childs.length < visibleCount){
                visibleCount = childs.length;
            }

            with(this.optionsListNode.style){
                display = "";
                height = ((visibleCount) ? (dojo.style.getOuterHeight(childs[0]) * visibleCount) : 0)+"px";
                //width = dojo.html.getOuterWidth(this.cbTableNode)+"px";
                width = dojo.html.getOuterWidth(this.textInputNode)-2+"px";
            }
            // only fadein once (flicker)
            if(!this._result_list_open){
                dojo.html.setOpacity(this.optionsListNode, 0);
                dojo.lfx.fadeIn(this.optionsListNode, this.fadeTime).play();
            }

            // prevent IE bleed through
            this._iframeTimer = dojo.lang.setTimeout(this, "sizeBackgroundIframe", 200);
            this._result_list_open = true;
        }else{
            this.hideResultList();
        }
    }
});
