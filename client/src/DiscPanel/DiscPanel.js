import React, {Component} from 'react';
import PropTypes from 'prop-types';

import {
    Button,
    Card,
    CardBody,
    CardTitle,
    Form,
    FormGroup,
    Input,
    Label,
    Table,
} from 'reactstrap';

import DiscInfo from '../DiscInfo';

import {
    actionDiscInfo,
    subscribeToDiscInfo,
} from '../api.js';


class DiscPanel extends Component {

    constructor(props) {
        super(props);
        this.state = {
            discInfo: {},
        };
        subscribeToDiscInfo(this.handleDriveInfo, this.props.driveId);
    }

    handleDriveInfo(discInfo) {
        this.setState({
            discInfo: discInfo,
        });
    }

    refreshDiscInfo() {
        actionDiscInfo(this.props.driveId);
    }

    render(){
        return(
            <div className="DiscPanel">
                <Card>
                    <CardBody>
                        <CardTitle>
                            [{ this.props.driveId }] { this.props.discTitle }
                        </CardTitle>
                        <Button>
                            <span className="glyphicon glyphicon-refresh"
                                  onClick={ this.refreshDiscInfo }
                                  />
                        </Button>
                    </CardBody>
                    <CardBody>
                        <DiscInfo { ...this.state.discInfo } />
                    </CardBody>
                </Card>
            </div>
        );
    }
}

DiscPanel.propTypes = {
    driveId: PropTypes.number.isRequired,
    discTitle: PropTypes.string.isRequired,
};

DiscPanel.defaultProps = {
};

export default DiscPanel;
