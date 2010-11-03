/*  Authors:
 *    Endi Sukma Dewata <edewata@redhat.com>
 *
 * Copyright (C) 2010 Red Hat
 * see file 'COPYING' for use and warranty information
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; version 2 only
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 */

/* REQUIRES: ipa.js, details.js, search.js, add.js, entity.js */

function ipa_hbac() {

    var that = ipa_entity({
        'name': 'hbac'
    });

    that.init = function() {

        that.create_add_dialog({
            'name': 'add',
            'title': 'Add New Rule',
            'init': ipa_hbac_add_init
        });

        that.create_search_facet({
            'name': 'search',
            'label': 'Search',
            'init': ipa_hbac_search_init,
            'setup': ipa_hbac_search_setup
        });

        that.create_details_facet({
            'name': 'details',
            'label': 'Details',
            'init': ipa_hbac_details_init
        });
    };

    that.init();

    return that;
}

IPA.add_entity(ipa_hbac());

function ipa_hbac_add_init() {
    this.create_field({name:'cn', label:'Rule Name'});
    this.create_field({name:'accessruletype', label:'Rule type (allow/deny)'});
}

function ipa_hbac_search_init() {

    this.create_column({name:'cn', label:'Rule Name'});
    this.create_column({name:'usercategory', label:'Who'});
    this.create_column({name:'hostcategory', label:'Accessing'});
    this.create_column({name:'servicecategory', label:'Via Service'});
    this.create_column({name:'sourcehostcategory', label:'From'});
    this.create_column({name:'ipaenabledflag', label:'Active'});

    this.create_column({
        name: 'quick_links',
        label: 'Quick Links',
        setup: ipa_hbac_quick_links
    });
}

function ipa_hbac_search_setup(container) {

    var that = this;

    that.filter = $.bbq.getState(that.entity_name + '-filter', true) || '';
/*
    // Not yet implemented

    var left_buttons = $('<span/>', {
        'style': 'float: left;'
    }).appendTo(container);

    left_buttons.append(ipa_button({
        'label': 'Troubleshoot Rules'
    }));

    left_buttons.append(ipa_button({
        'label': 'Cull Disabled Rules'
    }));

    var right_buttons = $('<span/>', {
        'style': 'float: right;'
    }).appendTo(container);

    right_buttons.append(ipa_button({
        'label': 'Login Services'
    }));

    right_buttons.append(ipa_button({
        'label': 'Login Svc Groups'
    }));

    container.append('<br/><br/>');
*/
    search_create(that.entity_name, that.columns, container);

    ipa_button({
        'label': IPA.messages.button.add,
        'icon': 'ui-icon-plus',
        'click': function() {
            var entity = IPA.get_entity(that.entity_name);
            entity.add_dialog.open();
            return false;
        }
    }).appendTo($('.search-controls', container));

    search_load(container, that.filter);
}

function ipa_hbac_quick_links(tr, attr, value, entry_attrs) {

    var column = this;
    var facet = column.facet;

    var pkey = IPA.metadata[column.entity_name].primary_key;
    var pkey_value = entry_attrs[pkey][0];

    var td = $('<td/>').appendTo(tr);

    $('<a/>', {
        'href': '#details',
        'title': 'Details',
        'text': 'Details',
        'click': function() {
            var state = {};
            state[column.entity_name+'-facet'] = 'details';
            state[column.entity_name+'-pkey'] = pkey_value;
            nav_push_state(state);
            return false;
        }
    }).appendTo(td);

    td.append(' | ');

    $('<a/>', {
        'href': '#test-rule',
        'title': 'Test Rule',
        'text': 'Test Rule',
        'click': function() {
            var state = {};
            state[column.entity_name+'-facet'] = 'test-rule';
            state[column.entity_name+'-pkey'] = pkey_value;
            nav_push_state(state);
            return false;
        }
    }).appendTo(td);
}

function ipa_hbac_details_init() {

    var that = this;
    var section;

    if (IPA.layout) {
        section = that.create_section({
            'name': 'general',
            'label': 'General',
            'template': 'hbac-details-general.html #contents'
        });

    } else {
        section = ipa_hbac_details_general_section({
            'name': 'general',
            'label': 'General'
        });
        that.add_section(section);
    }

    section.create_text({ 'name': 'cn', 'label': 'Name' });
    section.create_radio({ 'name': 'accessruletype', 'label': 'Rule Type' });
    section.create_textarea({ 'name': 'description', 'label': 'Description' });
    section.create_radio({ 'name': 'ipaenabledflag', 'label': 'Enabled' });

    if (IPA.layout) {
        section = that.create_section({
            'name': 'user',
            'label': 'Who',
            'template': 'hbac-details-user.html #contents'
        });

    } else {
        section = ipa_hbac_details_tables_section({
            'name': 'user',
            'label': 'Who',
            'text': 'Rule applies when access is requested by:',
            'field_name': 'usercategory',
            'options': [
                { 'value': 'all', 'label': 'Anyone' },
                { 'value': '', 'label': 'Specified Users and Groups' }
            ],
            'tables': [
                { 'field_name': 'memberuser_user' },
                { 'field_name': 'memberuser_group' }
            ]
        });
        that.add_section(section);
    }

    section.create_radio({ name: 'usercategory', label: 'User category' });
    section.add_field(ipa_hbac_association_widget({
        'id': that.entity_name+'-memberuser_user',
        'name': 'memberuser_user', 'label': 'Users',
        'other_entity': 'user', 'add_method': 'add_user', 'delete_method': 'remove_user'
    }));
    section.add_field(ipa_hbac_association_widget({
        'id': that.entity_name+'-memberuser_group',
        'name': 'memberuser_group', 'label': 'Groups',
        'other_entity': 'group', 'add_method': 'add_user', 'delete_method': 'remove_user'
    }));

    if (IPA.layout) {
        section = that.create_section({
            'name': 'host',
            'label': 'Accessing',
            'template': 'hbac-details-host.html #contents'
        });

    } else {
        section = ipa_hbac_details_tables_section({
            'name': 'host',
            'label': 'Accessing',
            'text': 'Rule applies when access is requested to:',
            'field_name': 'hostcategory',
            'options': [
                { 'value': 'all', 'label': 'Any Host' },
                { 'value': '', 'label': 'Specified Hosts and Groups' }
            ],
            'tables': [
                { 'field_name': 'memberhost_host' },
                { 'field_name': 'memberhost_hostgroup' }
            ],
            'columns': [
            ]
        });
        that.add_section(section);
    }

    section.create_radio({ 'name': 'hostcategory', 'label': 'Host category' });
    section.add_field(ipa_hbac_association_widget({
        'id': that.entity_name+'-memberhost_host',
        'name': 'memberhost_host', 'label': 'Hosts',
        'other_entity': 'host', 'add_method': 'add_host', 'delete_method': 'remove_host'
    }));
    section.add_field(ipa_hbac_association_widget({
        'id': that.entity_name+'-memberhost_hostgroup',
        'name': 'memberhost_hostgroup', 'label': 'Host Groups',
        'other_entity': 'hostgroup', 'add_method': 'add_host', 'delete_method': 'remove_host'
    }));

    if (IPA.layout) {
        section = that.create_section({
            'name': 'service',
            'label': 'Via Service',
            'template': 'hbac-details-service.html #contents'
        });

    } else {
        section = ipa_hbac_details_tables_section({
            'name': 'service',
            'label': 'Via Service',
            'text': 'Rule applies when access is requested via:',
            'field_name': 'servicecategory',
            'options': [
                { 'value': 'all', 'label': 'Any Service' },
                { 'value': '', 'label': 'Specified Services and Groups' }
            ],
            'tables': [
                { 'field_name': 'memberservice_hbacsvc' },
                { 'field_name': 'memberservice_hbacsvcgroup' }
            ]
        });
        that.add_section(section);
    }

    section.create_radio({ 'name': 'servicecategory', 'label': 'Service category' });
    section.add_field(ipa_hbac_association_widget({
        'id': that.entity_name+'-memberservice_hbacsvc',
        'name': 'memberservice_hbacsvc', 'label': 'Services',
        'other_entity': 'hbacsvc', 'add_method': 'add_service', 'delete_method': 'remove_service'
    }));
    section.add_field(ipa_hbac_association_widget({
        'id': that.entity_name+'-memberservice_hbacsvcgroup',
        'name': 'memberservice_hbacsvcgroup', 'label': 'Service Groups',
        'other_entity': 'hbacsvcgroup', 'add_method': 'add_service', 'delete_method': 'remove_service'
    }));

    if (IPA.layout) {
        section = that.create_section({
            'name': 'sourcehost',
            'label': 'From',
            'template': 'hbac-details-sourcehost.html #contents'
        });

    } else {
        section = ipa_hbac_details_tables_section({
            'name': 'sourcehost',
            'label': 'From',
            'text': 'Rule applies when access is being initiated from:',
            'field_name': 'sourcehostcategory',
            'options': [
                { 'value': 'all', 'label': 'Any Host' },
                { 'value': '', 'label': 'Specified Hosts and Groups' }
            ],
            'tables': [
                { 'field_name': 'sourcehost_host' },
                { 'field_name': 'sourcehost_hostgroup' }
            ]
        });
        that.add_section(section);
    }

    section.create_radio({ 'name': 'sourcehostcategory', 'label': 'Source host category' });
    section.add_field(ipa_hbac_association_widget({
        'id': that.entity_name+'-sourcehost_host',
        'name': 'sourcehost_host', 'label': 'Host',
        'other_entity': 'host', 'add_method': 'add_sourcehost', 'delete_method': 'remove_sourcehost'
    }));
    section.add_field(ipa_hbac_association_widget({
        'id': that.entity_name+'-sourcehost_hostgroup',
        'name': 'sourcehost_hostgroup', 'label': 'Host Groups',
        'other_entity': 'hostgroup', 'add_method': 'add_sourcehost', 'delete_method': 'remove_sourcehost'
    }));

    if (IPA.layout) {
        section = that.create_section({
            'name': 'accesstime',
            'label': 'When',
            'template': 'hbac-details-accesstime.html #contents'
        });

    } else {
        section = ipa_hbac_details_tables_section({
            'name': 'accesstime',
            'label': 'When',
            'text': 'Rule applies when access is being requested at:',
            'field_name': 'sourcehostcategory',
            'options': [
                { 'value': 'all', 'label': 'Any Time' },
                { 'value': '', 'label': 'Specified Times' }
            ],
            'tables': [
                { 'field_name': 'accesstime' }
            ]
        });
        that.add_section(section);
    }

    section.add_field(ipa_hbac_accesstime_widget({
        'id': that.entity_name+'-accesstime',
        'name': 'accesstime', 'label': 'Access Time'
    }));
}

function ipa_hbac_details_general_section(spec){

    spec = spec || {};

    var that = ipa_details_section(spec);

    that.create = function(container) {

        var table = $('<table/>', {
            'style': 'width: 100%;'
        }).appendTo(container);

        var tr = $('<tr/>', {
        }).appendTo(table);

        var td = $('<td/>', {
            'style': 'width: 100px; text-align: right;',
            'html': 'Name:'
        }).appendTo(tr);

        td = $('<td/>').appendTo(tr);

        $('<input/>', {
            'type': 'text',
            'name': 'cn',
            'size': 30
        }).appendTo(td);

        td = $('<td/>', {
            'style': 'text-align: right;'
        }).appendTo(tr);

        td.append('Rule type:');

        $('<input/>', {
            'type': 'radio',
            'name': 'accessruletype',
            'value': 'allow'
        }).appendTo(td);

        td.append('Allow');

        $('<input/>', {
            'type': 'radio',
            'name': 'accessruletype',
            'value': 'deny'
        }).appendTo(td);

        td.append('Deny');

        tr = $('<tr/>', {
        }).appendTo(table);

        td = $('<td/>', {
            'style': 'text-align: right; vertical-align: top;',
            'html': 'Description:'
        }).appendTo(tr);

        td = $('<td/>', {
            'colspan': 2
        }).appendTo(tr);

        $('<textarea/>', {
            'name': 'description',
            'rows': 5,
            'style': 'width: 100%'
        }).appendTo(td);

        tr = $('<tr/>', {
        }).appendTo(table);

        td = $('<td/>', {
            'style': 'text-align: right; vertical-align: top;',
            'html': 'Rule status:'
        }).appendTo(tr);

        td = $('<td/>', {
            'colspan': 2
        }).appendTo(tr);

        $('<input/>', {
            'type': 'radio',
            'name': 'ipaenabledflag',
            'value': 'TRUE'
        }).appendTo(td);

        td.append('Active');

        $('<input/>', {
            'type': 'radio',
            'name': 'ipaenabledflag',
            'value': 'FALSE'
        }).appendTo(td);

        td.append('Inactive');
    };

    return that;
}

function ipa_hbac_details_tables_section(spec){

    spec = spec || {};

    spec.create = create;

    var that = ipa_details_section(spec);

    that.text = spec.text;
    that.field_name = spec.field_name;
    that.options = spec.options;
    that.tables = spec.tables;
    that.columns = spec.columns;

    that.super_setup = that.super('setup');

    function create(container) {

        if (that.template) return;

        container.append(that.text);

        for (var i=0; i<that.options.length; i++) {
            var option = that.options[i];

            $('<input/>', {
                'type': 'radio',
                'name': that.field_name,
                'value': option.value
            }).appendTo(container);

            container.append(option.label);
        }

        container.append('<br/>');

        for (var i=0; i<that.tables.length; i++) {
            var table = that.tables[i];

            $('<div/>', {
                'id': that.entity_name+'-'+table.field_name
            }).appendTo(container);
        }
    }

    return that;
}

/**
 * This widget adds & deletes the rows of the table in the UI, but does not
 * execute IPA command to apply the changes on the server.
 */
function ipa_hbac_association_widget(spec) {

    spec = spec || {};

    spec.add = spec.add || add;
    spec.remove = spec.remove || remove;
    spec.save = spec.save || save;

    var that = ipa_table_widget(spec);

    that.other_entity = spec.other_entity;

    that.add_method = spec.add_method;
    that.delete_method = spec.delete_method;

    that.super_create = that.super('create');
    that.super_setup = that.super('setup');

    that.create = function(container) {

        // create a column when none defined
        if (!that.columns.length) {
            that.create_column({
                'name': that.name,
                'label': IPA.metadata[that.other_entity].label,
                'primary_key': true,
                'link': false
            });
        }

        that.super_create(container);

        var div = $('#'+that.id, container);

        var buttons = $('span[name=buttons]', div);
        if (buttons.children().length) {
            // widget loaded from template
            return;
        }

        $('<input/>', {
            'type': 'button',
            'name': 'remove',
            'value': 'Remove '+that.label
        }).appendTo(buttons);

        $('<input/>', {
            'type': 'button',
            'name': 'add',
            'value': 'Add '+that.label
        }).appendTo(buttons);
    };

    that.setup = function(container) {

        that.super_setup(container);

        var entity = IPA.get_entity(that.entity_name);
        var association = entity.get_association(that.other_entity);

        if (association && association.associator == 'serial') {
            that.associator = serial_associator;
        } else {
            that.associator = bulk_associator;
        }
    };

    function add(container) {

        var pkey = $.bbq.getState(that.entity_name + '-pkey', true) || '';
        var label = IPA.metadata[that.other_entity].label;
        var title = 'Add '+label+' to '+that.entity_name+' '+pkey;

        var dialog = ipa_adder_dialog({
            'name': 'adder_dialog',
            'title': title,
            'entity_name': that.entity_name,
            'pkey': pkey,
            'other_entity': that.other_entity,
            'associator': that.associator,
            'method': that.add_method,
            'on_success': function() {
                that.refresh(container);
                dialog.close();
            },
            'on_error': function() {
                that.refresh(container);
                dialog.close();
            }
        });

        dialog.open();
    }

    function remove(container) {

        var values = that.get_selected_values();

        if (!values.length) {
            alert('Select '+that.label+' to be removed.');
            return;
        }

        var pkey = $.bbq.getState(that.entity_name + '-pkey', true) || '';
        var label = IPA.metadata[that.other_entity].label;
        var title = 'Remove '+label+' from '+that.entity_name+' '+pkey;

        var dialog = ipa_deleter_dialog({
            'name': 'deleter_dialog',
            'title': title,
            'entity_name': that.entity_name,
            'pkey': pkey,
            'other_entity': that.other_entity,
            'values': values,
            'associator': that.associator,
            'method': that.delete_method,
            'on_success': function() {
                that.refresh(container);
                dialog.close();
            },
            'on_error': function() {
                that.refresh(container);
                dialog.close();
            }
        });

        dialog.open();
    }

    function save(container) {
        return [];
    }

    return that;
}

function ipa_hbac_accesstime_widget(spec) {

    spec = spec || {};

    spec.load = spec.load || load;
    spec.save = spec.save || save;

    var that = ipa_table_widget(spec);

    that.super_create = that.super('create');
    that.super_setup = that.super('setup');

    that.create = function(container) {

        // create a column when none defined
        if (!that.columns.length) {
            that.create_column({
                'name': that.name,
                'label': that.label,
                'primary_key': true,
                'link': false
            });
        }

        that.super_create(container);

        var div = $('#'+that.id);

        var buttons = $('span[name=buttons]', div);
        if (buttons.children().length) {
            // widget loaded from template
            return;
        }

        $('<input/>', {
            'type': 'button',
            'name': 'remove',
            'value': 'Remove '+that.label
        }).appendTo(buttons);

        $('<input/>', {
            'type': 'button',
            'name': 'add',
            'value': 'Add '+that.label
        }).appendTo(buttons);
    };

    function load(container, result) {
        var values = result[that.name] || '';

        if (values == '') {
            $('input[name="'+that.name+'"][value="all"]', container).attr('checked', 'checked');
        } else {
            $('input[name="'+that.name+'"][value=""]', container).attr('checked', 'checked');
        }

        that.tbody.empty();
        for (var i=0; i<values.length; i++) {
            var tr = that.row.clone();
            $('input[name="select"]', tr).val(values[i]);
            $('span[name="'+that.name+'"]', tr).html(values[i]);
            tr.appendTo(that.tbody);
        }
    }

    function save(container) {
        return [];
    }

    return that;
}
