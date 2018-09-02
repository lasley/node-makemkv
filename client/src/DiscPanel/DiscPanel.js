import React, {Component} from 'react';
import PropTypes from 'prop-types';

import {
    Button,
    Card,
    CardBody,
    CardTitle,
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
            discInfo: {}
        };
        subscribeToDiscInfo(this.handleDiscInfo, this, this.props.driveId);
    }

    handleDiscInfo(discInfo) {
        console.log('Got disc info');
        console.debug(discInfo);
        this.setState({
            discInfo: discInfo[this.props.driveId] || {},
        });
    }

    refreshDiscInfo() {
        actionDiscInfo(this.props.driveId);
    }

    render(){
        let discInfo = '';
        if (this.state.discInfo.tracks && this.state.discInfo.tracks.length > 0) {
            discInfo = <DiscInfo
                driveState={this.props.driveState}
                driveId={this.props.driveId}
                {...this.state.discInfo}
            />;
        }
        return(
            <div className="DiscPanel">
                <Card>
                    <CardBody>
                        <CardTitle>
                            <span>
                                {this.props.driveId}
                            </span>
                            &nbsp;-&nbsp;
                            <span>
                                {this.props.discName || 'No Disc'}
                            </span>
                        </CardTitle>
                        <Button onClick={() => this.refreshDiscInfo()}>
                            Refresh Disc
                        </Button>
                    </CardBody>
                    <CardBody>
                        {discInfo}
                    </CardBody>
                </Card>
            </div>
        );
    }
}

DiscPanel.propTypes = {
    driveId: PropTypes.number.isRequired,
    discName: PropTypes.string.isRequired,
    driveState: PropTypes.string.isRequired,
};

DiscPanel.defaultProps = {
};

export default DiscPanel;
