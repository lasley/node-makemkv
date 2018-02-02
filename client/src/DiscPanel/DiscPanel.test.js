import React from 'react';
import DiscPanel from './DiscPanel';
import renderer from 'react-test-renderer';

it('DiscPanel renders correctly', () => {
    const tree = renderer.create(
        <DiscPanel />
    ).toJSON();
    expect(tree).toMatchSnapshot();
});
