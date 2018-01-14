import React, {Component} from 'react';
import PropTypes from 'prop-types';

import {
    Button,
    Collapse,
    Form,
    FormGroup,
    Label,
    Input,
    Navbar,
    NavbarBrand,
} from 'reactstrap';


class Header extends Component {

    render(){
        return(
            <div className="Header">
                <Navbar color="inverse" inverse toggleable>
                    <NavbarBrand href="/">Node MakeMKV</NavbarBrand>
                    <Collapse navbar>
                        <Form inline>
                            <FormGroup>
                                <Label for="saveDirectory">
                                    Save Directory
                                </Label>
                                <Input type="text" id="saveDirectory" />
                            </FormGroup>
                        </Form>
                    </Collapse>
                </Navbar>
            </div>
        );
    }
}

Header.propTypes = {
};

Header.defaultProps = {
};

export default Header;
